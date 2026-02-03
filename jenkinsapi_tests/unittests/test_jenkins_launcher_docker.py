"""Tests for Docker-based Jenkins launcher functionality."""

import os
import subprocess
import tempfile
import pytest
from unittest import mock

from jenkinsapi.utils.jenkins_launcher import JenkinsLancher, FailedToStart


class TestJenkinsLauncherDockerDetection:
    """Test Docker availability detection."""

    def test_has_docker_available(self):
        """Test detection when Docker is available."""
        # Docker should be available in test environment
        result = JenkinsLancher._has_docker()
        # Result could be True or False depending on test environment
        assert isinstance(result, bool)

    @mock.patch("subprocess.run")
    def test_has_docker_returns_false_on_not_found(self, mock_run):
        """Test _has_docker returns False when docker command not found."""
        mock_run.side_effect = FileNotFoundError()
        assert JenkinsLancher._has_docker() is False

    @mock.patch("subprocess.run")
    def test_has_docker_returns_false_on_timeout(self, mock_run):
        """Test _has_docker returns False when command times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("docker", 5)
        assert JenkinsLancher._has_docker() is False


class TestJenkinsLauncherDockerStartup:
    """Test Docker container startup."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.systests_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp directories."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.systests_dir, ignore_errors=True)

    def test_launcher_initializes_without_error(self):
        """Test that JenkinsLauncher initializes correctly."""
        launcher = JenkinsLancher(
            self.temp_dir, self.systests_dir, "jenkins.war"
        )
        assert launcher is not None
        assert launcher.docker_container_id is None
        assert launcher.http_port > 0
        assert launcher.start_new_instance is True

    def test_launcher_with_explicit_jenkins_url(self):
        """Test that JenkinsLauncher respects explicit JENKINS_URL."""
        launcher = JenkinsLancher(
            self.temp_dir,
            self.systests_dir,
            "jenkins.war",
            jenkins_url="http://localhost:8080",
        )
        assert launcher.start_new_instance is False
        assert launcher.jenkins_url == "http://localhost:8080"

    @mock.patch("subprocess.run")
    def test_start_docker_jenkins_constructs_correct_command(self, mock_run):
        """Test that Docker run command is constructed correctly."""
        mock_run.return_value = mock.Mock(stdout="container-id-123\n")
        launcher = JenkinsLancher(
            self.temp_dir, self.systests_dir, "jenkins.war"
        )
        launcher.jenkins_home = self.temp_dir

        # Mock the block_until_jenkins_ready to avoid waiting
        with mock.patch.object(launcher, "block_until_jenkins_ready"):
            # Skip image checking to avoid additional subprocess.run calls
            with mock.patch.dict(os.environ, {"SKIP_IMAGE_CHECK": "1"}):
                launcher._start_docker_jenkins(timeout=10)

                # Verify docker run was called
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]

                # Check command structure
                assert call_args[0] == "docker"
                assert call_args[1] == "run"
                assert "-d" in call_args
                assert "-p" in call_args
                assert "-v" in call_args
                assert "-e" in call_args

                # Check that container ID is captured
                assert launcher.docker_container_id == "container-id-123"

    @mock.patch("subprocess.run")
    def test_start_docker_jenkins_with_custom_image(self, mock_run):
        """Test Docker startup with custom image via environment variable."""
        mock_run.return_value = mock.Mock(stdout="container-id-456\n")
        launcher = JenkinsLancher(
            self.temp_dir, self.systests_dir, "jenkins.war"
        )
        launcher.jenkins_home = self.temp_dir

        with mock.patch.object(
            launcher, "block_until_jenkins_ready"
        ) as mock_wait:
            # Skip image checking and set custom image
            with mock.patch.dict(
                os.environ,
                {
                    "JENKINS_DOCKER_IMAGE": "custom-jenkins:test",
                    "SKIP_IMAGE_CHECK": "1",
                },
            ):
                launcher._start_docker_jenkins(timeout=10)

                # Verify the image name is in the command
                call_args = mock_run.call_args[0][0]
                assert "custom-jenkins:test" in call_args

    @mock.patch("subprocess.run")
    def test_start_docker_jenkins_raises_on_failure(self, mock_run):
        """Test that docker startup failure raises FailedToStart."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "docker", stderr="Image not found"
        )
        launcher = JenkinsLancher(
            self.temp_dir, self.systests_dir, "jenkins.war"
        )
        launcher.jenkins_home = self.temp_dir

        # Skip image checking so error happens during docker run
        with mock.patch.dict(os.environ, {"SKIP_IMAGE_CHECK": "1"}):
            with pytest.raises(FailedToStart):
                launcher._start_docker_jenkins(timeout=10)

    @mock.patch("subprocess.run")
    def test_start_docker_jenkins_raises_on_timeout(self, mock_run):
        """Test that docker startup timeout raises FailedToStart."""
        mock_run.side_effect = subprocess.TimeoutExpired("docker", 30)
        launcher = JenkinsLancher(
            self.temp_dir, self.systests_dir, "jenkins.war"
        )
        launcher.jenkins_home = self.temp_dir

        # Skip image checking so timeout happens during docker run
        with mock.patch.dict(os.environ, {"SKIP_IMAGE_CHECK": "1"}):
            with pytest.raises(FailedToStart):
                launcher._start_docker_jenkins(timeout=10)


class TestJenkinsLauncherDockerStop:
    """Test Docker container stopping."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.systests_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp directories."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.systests_dir, ignore_errors=True)

    @mock.patch("subprocess.run")
    def test_stop_docker_jenkins_with_container(self, mock_run):
        """Test stopping Docker container."""
        launcher = JenkinsLancher(
            self.temp_dir, self.systests_dir, "jenkins.war"
        )
        launcher.docker_container_id = "container-id-123"
        launcher.jenkins_home = self.temp_dir

        launcher._stop_docker_jenkins()

        # Verify docker stop and rm were called
        assert mock_run.call_count == 2
        calls = mock_run.call_args_list

        # First call should be docker stop
        assert calls[0][0][0][:2] == ["docker", "stop"]
        # Second call should be docker rm
        assert calls[1][0][0][:2] == ["docker", "rm"]

        # Container ID should be cleared
        assert launcher.docker_container_id is None

    @mock.patch("subprocess.run")
    def test_stop_docker_jenkins_without_container(self, mock_run):
        """Test stopping when no container is running."""
        launcher = JenkinsLancher(
            self.temp_dir, self.systests_dir, "jenkins.war"
        )
        launcher.jenkins_home = self.temp_dir

        # Should not raise error
        launcher._stop_docker_jenkins()

        # Docker commands should not be called
        mock_run.assert_not_called()

    @mock.patch("subprocess.run")
    def test_stop_docker_jenkins_handles_timeout(self, mock_run):
        """Test that docker stop timeout is handled gracefully."""
        mock_run.side_effect = subprocess.TimeoutExpired("docker", 10)
        launcher = JenkinsLancher(
            self.temp_dir, self.systests_dir, "jenkins.war"
        )
        launcher.docker_container_id = "container-id-123"
        launcher.jenkins_home = self.temp_dir

        # Should not raise error
        launcher._stop_docker_jenkins()

        # Container ID should still be cleared
        assert launcher.docker_container_id is None


class TestJenkinsLauncherStartMethod:
    """Test the start() method - Docker only."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.systests_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp directories."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.systests_dir, ignore_errors=True)

        # Clean up environment variables
        os.environ.pop("JENKINS_URL", None)
        os.environ.pop("SKIP_DOCKER", None)
        os.environ.pop("JENKINS_DOCKER_IMAGE", None)

    @mock.patch.object(JenkinsLancher, "_start_docker_jenkins")
    def test_start_uses_docker(self, mock_docker_start):
        """Test that Docker is always used for new instances."""
        launcher = JenkinsLancher(self.temp_dir, self.systests_dir)

        launcher.start(timeout=10)

        # Docker start should be called
        mock_docker_start.assert_called_once_with(10)

    def test_start_skips_when_jenkins_url_set(self):
        """Test that explicit JENKINS_URL skips instance startup."""
        launcher = JenkinsLancher(
            self.temp_dir,
            self.systests_dir,
            jenkins_url="http://existing-jenkins:8080",
        )

        # When jenkins_url is set, start_new_instance should be False
        assert launcher.start_new_instance is False

        # Should not try to start anything
        launcher.start(timeout=10)

    @mock.patch.object(JenkinsLancher, "_start_docker_jenkins")
    def test_start_raises_on_docker_failure(self, mock_docker_start):
        """Test that Docker startup failure raises exception."""
        mock_docker_start.side_effect = FailedToStart("Docker failed")

        launcher = JenkinsLancher(self.temp_dir, self.systests_dir)

        with pytest.raises(FailedToStart):
            launcher.start(timeout=1)


class TestJenkinsLauncherStopMethod:
    """Test the stop() method - Docker only."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.systests_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp directories."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.systests_dir, ignore_errors=True)

    @mock.patch("subprocess.run")
    def test_stop_cleans_up_docker_container(self, mock_run):
        """Test that stop() cleans up Docker containers."""
        launcher = JenkinsLancher(self.temp_dir, self.systests_dir)
        launcher.docker_container_id = "container-id-123"

        launcher.stop()

        # Docker commands should have been called
        assert mock_run.call_count >= 2

    @mock.patch("subprocess.run")
    def test_stop_without_container(self, mock_run):
        """Test stop when no container is running."""
        launcher = JenkinsLancher(self.temp_dir, self.systests_dir)

        # Should not raise error
        launcher.stop()

        # Docker stop/rm should not be called if no container
        assert mock_run.call_count == 0
