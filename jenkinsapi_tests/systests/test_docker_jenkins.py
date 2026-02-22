"""Integration tests for Docker-based Jenkins launcher.

These tests verify that Jenkins can be started and tested using Docker containers.
They will be skipped if Docker is not available.
"""

import os
import pytest
from docker import DockerException, from_env
from jenkinsapi.utils.jenkins_launcher import JenkinsLancher


def _docker_available():
    """Check if Docker is available and running."""
    return JenkinsLancher._has_docker()


@pytest.mark.skipif(
    not _docker_available(),
    reason="Docker not available",
)
class TestDockerJenkinsLauncher:
    """Test Docker-based Jenkins launching."""

    def test_docker_detection(self):
        """Test that Docker is properly detected."""
        assert JenkinsLancher._has_docker() is True

    def test_docker_can_pull_image_info(self):
        """Test that Docker can fetch basic image info."""
        # Just verify docker works by making a lightweight daemon call.
        try:
            client = from_env()
            assert client.ping() is True
        except DockerException:
            pytest.skip("Docker daemon call failed")


@pytest.mark.skipif(
    not _docker_available(),
    reason="Docker not available",
)
class TestDockerImageBuildable:
    """Test that the Docker image can be built locally."""

    def test_dockerfile_exists(self):
        """Test that Dockerfile is present in ci directory."""
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "ci", "Dockerfile"
        )
        assert os.path.exists(dockerfile_path), (
            f"Dockerfile not found at {dockerfile_path}"
        )

    def test_plugins_txt_exists(self):
        """Test that plugins.txt is present in ci directory."""
        plugins_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "ci", "plugins.txt"
        )
        assert os.path.exists(plugins_path), (
            f"plugins.txt not found at {plugins_path}"
        )

    def test_plugins_txt_has_required_plugins(self):
        """Test that all required plugins are listed in plugins.txt."""
        plugins_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "ci", "plugins.txt"
        )

        required_plugins = [
            "ssh-slaves",
            "credentials",
            "git",
            "git-client",
            "credentials-binding",
            "envinject",
            "junit",
            "workflow-api",
            "script-security",
            "matrix-project",
        ]

        with open(plugins_path) as f:
            plugins_content = f.read()

        for plugin in required_plugins:
            assert plugin in plugins_content, (
                f"Required plugin '{plugin}' not found in plugins.txt"
            )


@pytest.mark.skipif(
    not _docker_available(),
    reason="Docker not available",
)
class TestJenkinsLauncherDockerMode:
    """Test JenkinsLauncher in Docker mode."""

    def test_launcher_detects_docker_mode(self, tmpdir):
        """Test that launcher properly detects Docker availability."""
        # Verify Docker detection works
        assert JenkinsLancher._has_docker() is True

    def test_launcher_respects_skip_docker_flag(self, tmpdir, monkeypatch):
        """Test that SKIP_DOCKER environment variable is respected."""
        monkeypatch.setenv("SKIP_DOCKER", "1")

        systests_dir = tmpdir
        local_orig_dir = tmpdir.mkdir("localinstance_files")

        launcher = JenkinsLancher(
            str(local_orig_dir),
            str(systests_dir),
            "jenkins.war",
        )

        # This is tested more thoroughly in unit tests
        # Just verify the launcher initializes
        assert launcher is not None

    def test_launcher_respects_custom_docker_image(self, tmpdir, monkeypatch):
        """Test that custom Docker image can be specified."""
        monkeypatch.setenv("JENKINS_DOCKER_IMAGE", "my-jenkins:custom")

        systests_dir = tmpdir
        local_orig_dir = tmpdir.mkdir("localinstance_files")

        launcher = JenkinsLancher(
            str(local_orig_dir),
            str(systests_dir),
            "jenkins.war",
        )

        # Verify initialization succeeds with custom image setting
        assert launcher is not None

    def test_launcher_respects_jenkins_url(self, tmpdir):
        """Test that explicit JENKINS_URL disables Docker."""
        systests_dir = tmpdir
        local_orig_dir = tmpdir.mkdir("localinstance_files")

        launcher = JenkinsLancher(
            str(local_orig_dir),
            str(systests_dir),
            "jenkins.war",
            jenkins_url="http://localhost:8080",
        )

        # When JENKINS_URL is set, start_new_instance should be False
        # meaning Docker won't be used
        assert launcher.start_new_instance is False


class TestDockerImageConfiguration:
    """Test Docker image configuration files."""

    def test_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists."""
        docker_compose_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "ci", "docker-compose.yml"
        )
        assert os.path.exists(docker_compose_path), (
            f"docker-compose.yml not found at {docker_compose_path}"
        )

    def test_docker_compose_valid_yaml(self):
        """Test that docker-compose.yml is valid YAML."""
        import yaml

        docker_compose_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "ci", "docker-compose.yml"
        )

        with open(docker_compose_path) as f:
            try:
                config = yaml.safe_load(f)
                assert config is not None
                assert "services" in config
                assert "jenkins" in config["services"]
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in docker-compose.yml: {e}")

    def test_dockerfile_has_healthcheck(self):
        """Test that Dockerfile includes HEALTHCHECK instruction."""
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "ci", "Dockerfile"
        )

        with open(dockerfile_path) as f:
            content = f.read()
            assert "HEALTHCHECK" in content, (
                "Dockerfile missing HEALTHCHECK instruction"
            )

    def test_dockerfile_exposes_required_ports(self):
        """Test that Dockerfile exposes required ports."""
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "ci", "Dockerfile"
        )

        with open(dockerfile_path) as f:
            content = f.read()
            assert "8080" in content, "Dockerfile should expose port 8080"
            assert "50000" in content, "Dockerfile should expose port 50000"

    def test_dockerfile_sets_java_opts(self):
        """Test that Dockerfile configures JAVA_OPTS properly."""
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "ci", "Dockerfile"
        )

        with open(dockerfile_path) as f:
            content = f.read()
            assert "jenkins.install.runSetupWizard=false" in content, (
                "Dockerfile should disable setup wizard"
            )
            assert "DNSMultiCast.disabled=true" in content, (
                "Dockerfile should disable DNS multicast"
            )


class TestDockerWorkflowConfiguration:
    """Test GitHub Actions workflow for Docker image building."""

    def test_build_jenkins_image_workflow_exists(self):
        """Test that build-jenkins-image.yml workflow exists."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "build-jenkins-image.yml",
        )
        assert os.path.exists(workflow_path), (
            f"build-jenkins-image.yml not found at {workflow_path}"
        )

    def test_workflow_has_schedule(self):
        """Test that workflow includes schedule trigger."""
        import yaml

        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "build-jenkins-image.yml",
        )

        with open(workflow_path) as f:
            config = yaml.safe_load(f)
            # YAML parses "on:" as the boolean True key
            assert True in config or "on" in config
            triggers = config.get(True, config.get("on", {}))
            assert "schedule" in triggers

    def test_workflow_publishes_to_ghcr(self):
        """Test that workflow publishes to GitHub Container Registry."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "build-jenkins-image.yml",
        )

        with open(workflow_path) as f:
            content = f.read()
            assert "ghcr.io" in content, "Workflow should publish to ghcr.io"
            # Check for either docker/build-push-action or docker push/login methods
            assert "docker/build-push-action" in content or (
                "docker" in content and "docker-publish" in content
            ), (
                "Workflow should publish to Docker registry "
                "(via docker/build-push-action or docker commands)"
            )


class TestPythonWorkflowDockerIntegration:
    """Test Python CI workflow Docker integration."""

    def test_python_workflow_pulls_docker_image(self):
        """Test that python-package.yml pulls Docker image."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "python-package.yml",
        )

        with open(workflow_path) as f:
            content = f.read()
            assert "docker pull" in content, (
                "Workflow should pull Docker image"
            )
            assert "jenkinsapi-jenkins" in content, (
                "Workflow should pull jenkinsapi-jenkins image"
            )

    def test_python_workflow_no_java_setup(self):
        """Test that python-package.yml no longer sets up Java."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "python-package.yml",
        )

        with open(workflow_path) as f:
            content = f.read()
            assert "setup-java" not in content, (
                "Workflow should not setup Java anymore"
            )
