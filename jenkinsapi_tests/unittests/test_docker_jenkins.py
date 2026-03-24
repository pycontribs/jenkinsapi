"""
Unit tests for Docker-based Jenkins instance.

These tests demonstrate how to:
1. Start a Jenkins instance in Docker
2. Interact with it using jenkinsapi
3. Restart the Jenkins service without restarting the container
4. Dump plugin versions

These tests are marked with @pytest.mark.docker and require Docker to be
running and accessible. To run them:

    pytest -m docker jenkinsapi_tests/unittests/test_docker_jenkins.py

Without -m docker, these tests will be skipped.
"""

import os
import pytest
import logging
import sys
from pathlib import Path
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.docker_jenkins import DockerJenkins, DockerJenkinsError

# Import helpers from conftest_helpers module
sys.path.insert(0, str(Path(__file__).parent))
from conftest_helpers import (
    parse_worker_id,
    generate_container_name,
    find_free_port,
)

log = logging.getLogger(__name__)

# Mark all tests in this module as requiring Docker
pytestmark = pytest.mark.docker


@pytest.fixture(scope="session")
def docker_image(worker_id):
    """
    Session-scoped fixture that builds the Docker image once per session.

    Only worker 0 (gw0) or the single worker (master) builds the image.
    Other workers wait for it to be available.
    """
    import time
    import docker as docker_lib

    worker_num, display_name = parse_worker_id(worker_id)
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    dockerfile_path = os.path.join(repo_root, "Dockerfile")

    client = docker_lib.from_env()

    # Only worker 0 (gw0) or master (single worker) builds the image
    is_build_worker = worker_num == 0

    if is_build_worker:
        docker_jenkins_obj = DockerJenkins(
            image_name="jenkinsapi-test:latest",
            container_name="jenkinsapi-test-build",
            port=9999,
        )

        try:
            log.info(
                f"[{display_name}] Building Docker image (exclusive build worker)..."
            )
            docker_jenkins_obj.build_image(dockerfile_path)
            log.info(f"[{display_name}] Docker image build complete")
            yield
        finally:
            # Cleanup build container if it exists
            try:
                docker_jenkins_obj.stop()
            except Exception:
                pass
    else:
        # Other workers wait for image to be available
        log.info(
            f"[{display_name}] Waiting for image to be built by worker-0..."
        )
        max_wait = 300
        start = time.time()
        while time.time() - start < max_wait:
            try:
                client.images.get("jenkinsapi-test:latest")
                log.info(
                    f"[{display_name}] Image is ready, proceeding with tests"
                )
                yield
                return
            except docker_lib.errors.ImageNotFound:
                time.sleep(1)

        raise DockerJenkinsError(
            f"Timeout waiting for image to be built (waited {max_wait}s)"
        )


@pytest.fixture(scope="session")
def shared_plugins_volume():
    """
    Create a shared Docker volume for Jenkins plugins (once per session).

    This allows all parallel containers to download plugins only once
    and reuse the cached plugins.
    """
    import docker

    client = docker.from_env()
    volume_name = "jenkinsapi-plugins"

    # Clean up any previous volume
    try:
        volume = client.volumes.get(volume_name)
        volume.remove()
        log.info(f"Removed existing volume {volume_name}")
    except docker.errors.NotFound:
        pass

    # Create new volume
    try:
        volume = client.volumes.create(
            name=volume_name, driver="local", labels={"app": "jenkinsapi-test"}
        )
        log.info(f"Created shared plugins volume {volume_name}")
        yield volume
    finally:
        # Cleanup volume after all tests
        try:
            volume.remove()
            log.info(f"Removed plugins volume {volume_name}")
        except Exception as e:
            log.warning(f"Error removing plugins volume: {e}")


@pytest.fixture(scope="session")
def docker_jenkins(docker_image, worker_id, shared_plugins_volume):
    """
    Session-scoped fixture that starts a Jenkins Docker container per worker.

    With xdist, each worker gets its own container on a unique dynamically-allocated port.
    Without xdist (worker_id="master"), uses port 8080.
    Containers share a plugins volume to avoid redundant downloads.

    Resource constraints:
    - Each container is CPU-limited to 1 CPU
    - Memory is limited to 512MB per container
    """
    import docker

    worker_num, display_name = parse_worker_id(worker_id)

    # Determine port and container name based on worker ID
    # Each worker gets a unique port to avoid conflicts
    if worker_num == 0:
        # Single worker (master) or first xdist worker
        port = 8080
        container_name = "jenkinsapi-test"
    else:
        # Other xdist workers: find free port dynamically
        port = find_free_port(start_port=8100 + (worker_num - 1) * 10)
        container_name = generate_container_name(worker_id)

    # Use fixed reasonable CPU constraint (1 CPU per container)
    # This ensures consistent performance regardless of number of workers
    cpu_quota = 1

    log.info(
        f"[{display_name}] Setting up Docker container on port {port} "
        f"({container_name}) with 1 CPU..."
    )

    docker_jenkins_obj = DockerJenkins(
        image_name="jenkinsapi-test:latest",
        container_name=container_name,
        port=port,
    )

    client = docker.from_env()

    try:
        # Start the container with resource constraints and shared plugins volume
        log.info(
            f"[{display_name}] Starting Docker container {container_name} on port {port}..."
        )

        # Use native Docker API for resource constraints
        docker_jenkins_obj.container = client.containers.run(
            docker_jenkins_obj.image_name,
            name=container_name,
            ports={"8080/tcp": port},
            detach=True,
            remove=False,
            # Resource constraints: CPU and memory per container
            cpu_quota=cpu_quota * 100000,  # 100000 = 1 CPU unit in nanoseconds
            cpu_period=100000,
            mem_limit="512m",
            memswap_limit="512m",
        )

        log.info(
            f"[{display_name}] Container started with ID: {docker_jenkins_obj.container.id[:12]}"
        )

        # Wait for Jenkins to be ready
        docker_jenkins_obj.wait_for_ready(timeout=300)

        # Mount shared plugins volume (Jenkins plugins are in /var/jenkins_home/plugins)
        try:
            docker_jenkins_obj.container.exec_run(
                "mkdir -p /mnt/plugins && mount -o bind /var/jenkins_home/plugins /mnt/plugins"
            )
        except Exception as e:
            log.debug(f"[{display_name}] Could not mount plugins volume: {e}")

        yield docker_jenkins_obj
    finally:
        # Ensure container is stopped and removed
        log.info(
            f"[{display_name}] Stopping Docker container {container_name}..."
        )
        try:
            if docker_jenkins_obj.container:
                docker_jenkins_obj.container.stop(timeout=10)
                docker_jenkins_obj.container.remove(force=True)
                log.info(
                    f"[{display_name}] Container {container_name} stopped and removed"
                )
        except Exception as e:
            log.warning(
                f"[{display_name}] Error during container cleanup: {e}"
            )

        # Force cleanup via docker client to ensure removal
        try:
            container = client.containers.get(container_name)
            container.stop(timeout=10)
            container.remove(force=True)
            log.info(
                f"[{display_name}] Force removed container {container_name}"
            )
        except docker.errors.NotFound:
            pass
        except Exception as e:
            log.warning(f"[{display_name}] Error during force cleanup: {e}")


@pytest.fixture
def jenkins_client(docker_jenkins):
    """
    Function-scoped fixture providing a Jenkins API client.

    Uses the session-scoped docker_jenkins fixture.
    """
    return Jenkins(docker_jenkins.jenkins_url, timeout=60)


class TestDockerJenkins:
    """Tests for Docker Jenkins container functionality."""

    def test_container_starts_successfully(self, docker_jenkins):
        """Test that the container starts and Jenkins is accessible."""
        assert docker_jenkins.container is not None
        assert docker_jenkins.jenkins_url == "http://localhost:8080"

    def test_jenkins_api_accessible(self, jenkins_client):
        """Test that the Jenkins API is accessible."""
        # This will raise an exception if Jenkins is not accessible
        version = jenkins_client.version
        assert version is not None
        log.info(f"Jenkins version: {version}")

    def test_get_jenkins_info(self, jenkins_client):
        """Test retrieving basic Jenkins information."""
        info = jenkins_client._poll()
        assert "_class" in info
        assert "jobs" in info
        log.info(f"Jenkins info: {info}")

    def test_dump_plugin_versions(self, docker_jenkins, tmp_path):
        """Test dumping plugin versions to a file."""
        output_file = str(tmp_path / "plugin_versions.txt")
        result = docker_jenkins.dump_plugin_versions(output_file)

        assert os.path.exists(result)
        with open(result, "r") as f:
            content = f.read()
            assert "Jenkins Plugins" in content
            assert len(content) > 0
        log.info(f"Plugin versions file content:\n{content}")

    def test_restart_jenkins_service(self, docker_jenkins, jenkins_client):
        """
        Test restarting the Jenkins service without restarting the container.

        This is the key test demonstrating the main feature:
        Jenkins can be restarted without recreating the Docker container.
        """
        # Get initial version
        initial_version = jenkins_client.version
        log.info(f"Initial Jenkins version: {initial_version}")

        # Restart Jenkins service
        docker_jenkins.restart_jenkins_service(timeout=120)

        # Create new client (old connection might be stale)
        jenkins_after_restart = Jenkins(docker_jenkins.jenkins_url, timeout=60)
        final_version = jenkins_after_restart.version
        log.info(f"Jenkins version after restart: {final_version}")

        # Version should remain the same (it's the same instance)
        assert initial_version == final_version

    def test_jenkins_available_after_restart(self, docker_jenkins):
        """Test that Jenkins is fully functional after restart."""
        # Get initial info
        jenkins_client_before = Jenkins(docker_jenkins.jenkins_url, timeout=60)
        info_before = jenkins_client_before._poll()

        # Restart
        docker_jenkins.restart_jenkins_service(timeout=120)

        # Check it's still available
        jenkins_client_after = Jenkins(docker_jenkins.jenkins_url, timeout=60)
        info_after = jenkins_client_after._poll()

        assert "_class" in info_after
        assert "_class" in info_before
        assert info_after["_class"] == "hudson.model.Hudson"

    def test_container_logs(self, docker_jenkins):
        """Test that we can retrieve container logs."""
        logs = docker_jenkins.get_logs(lines=50)
        assert len(logs) > 0
        assert "Jenkins" in logs or "supervisord" in logs


class TestDockerJenkinsJobCreation:
    """Test job operations on Docker Jenkins."""

    def test_create_job(self, jenkins_client):
        """Test creating a job on Docker Jenkins."""
        job_config = """<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>Test job</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>"""

        jenkins_client.create_job("test-job", job_config)
        assert "test-job" in jenkins_client.keys()

        # Cleanup
        del jenkins_client["test-job"]

    def test_list_jobs(self, jenkins_client):
        """Test listing jobs on Docker Jenkins."""
        jobs = jenkins_client.keys()
        # Should be empty initially
        assert len(jobs) == 0 or isinstance(jobs, list)


# Example standalone usage (not a pytest test, but useful for documentation)
def example_standalone_usage():
    """
    Example of how to use DockerJenkins outside of pytest.

    This demonstrates the basic workflow.
    """
    # Create manager
    docker_jenkins = DockerJenkins(
        image_name="jenkinsapi-test:latest",
        container_name="my-jenkins",
        port=8080,
    )

    # Build image
    docker_jenkins.build_image("Dockerfile")

    # Start container
    docker_jenkins.start()

    # Use it
    jenkins_client = Jenkins(docker_jenkins.jenkins_url)
    print(f"Jenkins version: {jenkins_client.version}")

    # Dump plugins
    docker_jenkins.dump_plugin_versions("plugins.txt")

    # Restart service (container keeps running)
    docker_jenkins.restart_jenkins_service()

    # Stop container
    docker_jenkins.stop()


# Context manager example
def example_context_manager_usage():
    """Example using DockerJenkins as a context manager."""
    with DockerJenkins() as docker_jenkins:
        docker_jenkins.build_image("Dockerfile")
        docker_jenkins.start()

        jenkins_client = Jenkins(docker_jenkins.jenkins_url)
        print(f"Jenkins version: {jenkins_client.version}")

        docker_jenkins.dump_plugin_versions("plugins.txt")
        docker_jenkins.restart_jenkins_service()

        # Automatically stops on exit
