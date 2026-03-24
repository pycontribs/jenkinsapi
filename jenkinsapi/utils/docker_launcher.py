"""
Docker-based Jenkins launcher for system tests.

This launcher uses Docker to run Jenkins, providing a faster and more
reliable alternative to downloading and running Jenkins locally.
"""

import logging
from typing import Optional, List

from jenkinsapi.utils.docker_jenkins import DockerJenkins

log = logging.getLogger(__name__)


class DockerLauncher:
    """Launch Jenkins in Docker for testing."""

    def __init__(
        self,
        image_name: str = "jenkinsapi-test:latest",
        container_name: str = "jenkinsapi-systest",
        port: int = 8080,
        dockerfile_path: str = "Dockerfile",
        jenkins_url: Optional[str] = None,
    ):
        """
        Initialize Docker launcher.

        Args:
            image_name: Docker image name
            container_name: Container name
            port: Port to expose Jenkins on
            dockerfile_path: Path to Dockerfile
            jenkins_url: Override Jenkins URL (for external Jenkins)
        """
        self.image_name = image_name
        self.container_name = container_name
        self.port = port
        self.dockerfile_path = dockerfile_path
        self.docker_jenkins = None

        # If external Jenkins URL provided, skip Docker
        if jenkins_url:
            self.jenkins_url = jenkins_url
            self.docker_jenkins = None
            log.info(f"Using external Jenkins at {jenkins_url}")
        else:
            self.jenkins_url = None

    def start(self, timeout: int = 300):
        """
        Start Jenkins in Docker.

        Args:
            timeout: Time to wait for Jenkins to be ready
        """
        # If external Jenkins, nothing to do
        if self.docker_jenkins is None and self.jenkins_url:
            return

        # Create and start Docker Jenkins
        self.docker_jenkins = DockerJenkins(
            image_name=self.image_name,
            container_name=self.container_name,
            port=self.port,
        )

        log.info("Building Docker image...")
        self.docker_jenkins.build_image(self.dockerfile_path)

        log.info(f"Starting Jenkins in Docker on port {self.port}...")
        self.docker_jenkins.start(timeout=timeout)

        self.jenkins_url = self.docker_jenkins.jenkins_url
        log.info(f"Jenkins ready at {self.jenkins_url}")

    def stop(self):
        """Stop Jenkins Docker container."""
        if self.docker_jenkins:
            log.info("Stopping Jenkins Docker container...")
            try:
                self.docker_jenkins.stop()
            except Exception as e:
                log.warning(f"Error stopping Docker container: {e}")

    def restart(self, timeout: int = 120):
        """
        Restart Jenkins service without restarting the container.

        Args:
            timeout: Time to wait for Jenkins to be ready after restart
        """
        if self.docker_jenkins:
            log.info("Restarting Jenkins service...")
            self.docker_jenkins.restart_jenkins_service(timeout=timeout)
