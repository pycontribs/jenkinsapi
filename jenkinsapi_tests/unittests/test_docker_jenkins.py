"""Tests for Docker-based Jenkins (requires Docker running)."""

import io
import os
import logging
import tarfile

import pytest

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.docker_jenkins import (
    DEFAULT_IMAGE_NAME,
    DockerJenkins,
    DockerJenkinsError,
)
from jenkinsapi_tests.unittests.conftest_helpers import (
    parse_worker_id,
    generate_container_name,
    find_free_port,
)

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def _docker_client_or_skip():
    import docker as docker_lib

    try:
        client = docker_lib.from_env()
        client.ping()
        return client
    except docker_lib.errors.DockerException as exc:
        pytest.skip(f"Docker daemon unavailable: {exc}")


@pytest.fixture(scope="session")
def docker_image(worker_id):
    """Build the shared Docker image once per test session."""
    import docker as docker_lib

    worker_num, display_name = parse_worker_id(worker_id)
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    dockerfile_path = os.path.join(repo_root, "docker", "Dockerfile")
    client = _docker_client_or_skip()

    try:
        client.images.get(DEFAULT_IMAGE_NAME)
        log.info("[%s] Docker image already exists", display_name)
        return DEFAULT_IMAGE_NAME
    except docker_lib.errors.ImageNotFound:
        pass

    docker_jenkins = DockerJenkins(
        image_name=DEFAULT_IMAGE_NAME,
        container_name="jenkinsapi-test-build",
        port=9999,
    )
    if worker_num == 0:
        log.info("[%s] Building Docker image...", display_name)
        docker_jenkins.build_image(dockerfile_path)
        return docker_jenkins.image_name

    log.info("[%s] Waiting for image from worker-0...", display_name)
    import time

    start = time.time()
    while time.time() - start < 300:
        try:
            client.images.get(docker_jenkins.image_name)
            return docker_jenkins.image_name
        except docker_lib.errors.ImageNotFound:
            time.sleep(1)
    raise DockerJenkinsError("Timeout waiting for image to be built")


@pytest.fixture(scope="session")
def docker_jenkins(docker_image, worker_id):
    """Start one Jenkins container per xdist worker."""
    worker_num, display_name = parse_worker_id(worker_id)
    base_port = 8080 if worker_num == 0 else 8100 + (worker_num - 1) * 10
    port = find_free_port(start_port=base_port)
    container_name = generate_container_name(
        worker_id, base_name="jenkinsapi-systest"
    )

    log.info(
        "[%s] Starting container %s on port %d...",
        display_name,
        container_name,
        port,
    )

    dj = DockerJenkins(
        image_name=docker_image,
        container_name=container_name,
        port=port,
    )

    try:
        dj.start(timeout=300)
        yield dj
    finally:
        try:
            dj.stop()
        except Exception as e:
            log.warning("[%s] Error during cleanup: %s", display_name, e)


@pytest.fixture
def jenkins_client(docker_jenkins):
    return Jenkins(docker_jenkins.jenkins_url, timeout=60)


class TestDockerJenkins:
    def test_dump_plugin_versions_extracts_text_file(self, tmp_path):
        plugin_text = "Jenkins Plugins\nworkflow-job:latest\n"
        archive_buffer = io.BytesIO()
        with tarfile.open(fileobj=archive_buffer, mode="w") as archive:
            member = tarfile.TarInfo(name="plugin_versions.txt")
            member.size = len(plugin_text.encode())
            archive.addfile(member, io.BytesIO(plugin_text.encode()))

        class FakeResult:
            exit_code = 0
            output = b""

        class FakeContainer:
            def exec_run(self, command):
                assert command == (
                    "/usr/local/bin/dump-plugin-versions plugin_versions.txt"
                )
                return FakeResult()

            def get_archive(self, path):
                assert path == "plugin_versions.txt"
                return iter([archive_buffer.getvalue()]), {}

        docker_jenkins = DockerJenkins.__new__(DockerJenkins)
        docker_jenkins.container = FakeContainer()

        output_file = tmp_path / "plugin_versions.txt"
        result = docker_jenkins.dump_plugin_versions(str(output_file))

        assert result == str(output_file)
        assert output_file.read_text() == plugin_text

    def test_container_starts_successfully(self, docker_jenkins):
        assert docker_jenkins.container is not None
        assert docker_jenkins.jenkins_url.startswith("http://localhost:")

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
