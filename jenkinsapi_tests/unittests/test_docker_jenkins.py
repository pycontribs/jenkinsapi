"""Tests for Docker-based Jenkins (requires Docker running). Run with: pytest -m docker"""

import os
import pytest
import logging
import sys
from pathlib import Path
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.docker_jenkins import DockerJenkins, DockerJenkinsError

sys.path.insert(0, str(Path(__file__).parent))
from conftest_helpers import (
    parse_worker_id,
    generate_container_name,
    find_free_port,
)

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


@pytest.fixture(scope="session")
def docker_image(worker_id):
    """Build image once per session; only worker 0 builds, others wait."""
    import time
    import docker as docker_lib

    worker_num, display_name = parse_worker_id(worker_id)
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    dockerfile_path = os.path.join(repo_root, "docker", "Dockerfile")

    client = docker_lib.from_env()

    if worker_num == 0:
        dj = DockerJenkins(
            image_name="jenkinsapi-test:latest",
            container_name="jenkinsapi-test-build",
            port=9999,
        )
        try:
            log.info("[%s] Building Docker image...", display_name)
            dj.build_image(dockerfile_path)
            yield
        finally:
            try:
                dj.stop()
            except Exception:
                pass
    else:
        log.info("[%s] Waiting for image from worker-0...", display_name)
        start = time.time()
        while time.time() - start < 300:
            try:
                client.images.get("jenkinsapi-test:latest")
                yield
                return
            except docker_lib.errors.ImageNotFound:
                time.sleep(1)
        raise DockerJenkinsError("Timeout waiting for image to be built")


@pytest.fixture(scope="session")
def shared_plugins_volume():
    """Create a shared Docker volume for Jenkins plugins."""
    import docker

    client = docker.from_env()
    volume_name = "jenkinsapi-plugins"

    try:
        client.volumes.get(volume_name).remove()
    except docker.errors.NotFound:
        pass

    volume = client.volumes.create(
        name=volume_name, driver="local", labels={"app": "jenkinsapi-test"}
    )
    try:
        yield volume
    finally:
        try:
            volume.remove()
        except Exception as e:
            log.warning("Error removing plugins volume: %s", e)


@pytest.fixture(scope="session")
def docker_jenkins(docker_image, worker_id, shared_plugins_volume):
    """Start one Jenkins container per xdist worker."""
    import docker

    worker_num, display_name = parse_worker_id(worker_id)

    if worker_num == 0:
        port = 8080
        container_name = "jenkinsapi-test"
    else:
        port = find_free_port(start_port=8100 + (worker_num - 1) * 10)
        container_name = generate_container_name(worker_id)

    log.info(
        "[%s] Starting container %s on port %d...",
        display_name,
        container_name,
        port,
    )

    dj = DockerJenkins(
        image_name="jenkinsapi-test:latest",
        container_name=container_name,
        port=port,
    )
    client = docker.from_env()

    try:
        dj.container = client.containers.run(
            dj.image_name,
            name=container_name,
            ports={"8080/tcp": port},
            detach=True,
            remove=False,
            cpu_quota=100000,
            cpu_period=100000,
            mem_limit="512m",
            memswap_limit="512m",
        )
        dj.wait_for_ready(timeout=300)

        try:
            dj.container.exec_run(
                "mkdir -p /mnt/plugins && mount -o bind /var/jenkins_home/plugins /mnt/plugins"
            )
        except Exception:
            pass

        yield dj
    finally:
        try:
            if dj.container:
                dj.container.stop(timeout=10)
                dj.container.remove(force=True)
        except Exception as e:
            log.warning("[%s] Error during cleanup: %s", display_name, e)

        try:
            client.containers.get(container_name).remove(force=True)
        except docker.errors.NotFound:
            pass
        except Exception as e:
            log.warning("[%s] Error during force cleanup: %s", display_name, e)


@pytest.fixture
def jenkins_client(docker_jenkins):
    return Jenkins(docker_jenkins.jenkins_url, timeout=60)


class TestDockerJenkins:
    def test_container_starts_successfully(self, docker_jenkins):
        assert docker_jenkins.container is not None
        assert docker_jenkins.jenkins_url == "http://localhost:8080"

    def test_jenkins_api_accessible(self, jenkins_client):
        assert jenkins_client.version is not None

    def test_get_jenkins_info(self, jenkins_client):
        info = jenkins_client._poll()
        assert "_class" in info
        assert "jobs" in info

    def test_dump_plugin_versions(self, docker_jenkins, tmp_path):
        output_file = str(tmp_path / "plugin_versions.txt")
        result = docker_jenkins.dump_plugin_versions(output_file)
        assert os.path.exists(result)
        with open(result) as f:
            content = f.read()
        assert "Jenkins Plugins" in content

    def test_restart_jenkins_service(self, docker_jenkins, jenkins_client):
        initial_version = jenkins_client.version
        docker_jenkins.restart_jenkins_service(timeout=120)
        assert (
            Jenkins(docker_jenkins.jenkins_url, timeout=60).version
            == initial_version
        )

    def test_jenkins_available_after_restart(self, docker_jenkins):
        docker_jenkins.restart_jenkins_service(timeout=120)
        info = Jenkins(docker_jenkins.jenkins_url, timeout=60)._poll()
        assert info.get("_class") == "hudson.model.Hudson"

    def test_container_logs(self, docker_jenkins):
        logs = docker_jenkins.get_logs(lines=50)
        assert len(logs) > 0
        assert "Jenkins" in logs or "supervisord" in logs


class TestDockerJenkinsJobCreation:
    def test_create_job(self, jenkins_client):
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
        del jenkins_client["test-job"]

    def test_list_jobs(self, jenkins_client):
        jobs = jenkins_client.keys()
        assert len(jobs) == 0 or isinstance(jobs, list)
