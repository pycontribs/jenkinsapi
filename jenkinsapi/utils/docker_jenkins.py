"""
Docker-based Jenkins instance manager for testing.

This module provides a way to run Jenkins in Docker with the ability to
restart the Jenkins service without restarting the container, which is
useful for testing restart behavior.
"""

import os
import time
import logging
import docker
import requests
from typing import Optional
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

log = logging.getLogger(__name__)


class DockerJenkinsError(Exception):
    """Base exception for Docker Jenkins operations."""

    pass


class DockerJenkins:
    """Manage a Jenkins instance running in Docker."""

    def __init__(
        self,
        image_name: str = "jenkinsapi-test:latest",
        container_name: str = "jenkinsapi-test",
        port: int = 8080,
        jenkins_home: Optional[str] = None,
    ):
        """
        Initialize Docker Jenkins manager.

        Args:
            image_name: Docker image name to use
            container_name: Name for the container
            port: Port to expose Jenkins on (default: 8080)
            jenkins_home: Path to mount as JENKINS_HOME (default: Docker volume)
        """
        self.image_name = image_name
        self.container_name = container_name
        self.port = port
        self.jenkins_home = jenkins_home
        self.client = docker.from_env()
        self.container = None
        self.jenkins_url = f"http://localhost:{port}"

    def build_image(self, dockerfile_path: str = "Dockerfile") -> bool:
        """
        Build the Docker image from Dockerfile.

        Args:
            dockerfile_path: Path to Dockerfile

        Returns:
            True if successful
        """
        # Check if image already exists
        try:
            self.client.images.get(self.image_name)
            log.info(
                f"Docker image {self.image_name} already exists, skipping build"
            )
            return True
        except docker.errors.ImageNotFound:
            pass

        if not os.path.exists(dockerfile_path):
            raise DockerJenkinsError(
                f"Dockerfile not found: {dockerfile_path}"
            )

        log.info(
            f"Building Docker image {self.image_name} from {dockerfile_path}"
        )
        try:
            self.client.images.build(
                path=os.path.dirname(os.path.abspath(dockerfile_path)),
                dockerfile=os.path.basename(dockerfile_path),
                tag=self.image_name,
            )
            log.info(f"Successfully built image {self.image_name}")
            return True
        except docker.errors.BuildError as e:
            raise DockerJenkinsError(f"Failed to build image: {e}")

    def start(self, timeout: int = 300) -> None:
        """
        Start the Jenkins container.

        Args:
            timeout: Maximum time to wait for Jenkins to be ready (seconds)
        """
        # Stop existing container if running
        try:
            existing = self.client.containers.get(self.container_name)
            log.info(f"Stopping existing container {self.container_name}")
            existing.stop()
            existing.remove()
        except docker.errors.NotFound:
            pass

        # Prepare volumes
        volumes = {}
        if self.jenkins_home:
            volumes = {
                self.jenkins_home: {"bind": "/var/jenkins_home", "mode": "rw"}
            }

        log.info(f"Starting Jenkins container {self.container_name}")
        try:
            self.container = self.client.containers.run(
                self.image_name,
                name=self.container_name,
                ports={"8080/tcp": self.port},
                volumes=volumes,
                detach=True,
                remove=False,
            )
            log.info(f"Container started with ID: {self.container.id[:12]}")
        except docker.errors.ImageNotFound:
            raise DockerJenkinsError(
                f"Image not found: {self.image_name}. "
                "Please build it first with build_image()"
            )
        except (docker.errors.ContainerError, docker.errors.APIError) as e:
            msg = str(e).lower()
            if "port" in msg and (
                "already allocated" in msg or "address already in use" in msg
            ):
                raise DockerJenkinsError(
                    f"Port conflict on port {self.port}: {e}"
                )
            raise DockerJenkinsError(f"Failed to start container: {e}")

        # Wait for Jenkins to be ready
        self.wait_for_ready(timeout)

    def stop(self) -> None:
        """Stop and remove the Jenkins container."""
        if self.container:
            log.info(f"Stopping container {self.container_name}")
            try:
                self.container.stop(timeout=10)
                self.container.remove()
                log.info("Container stopped")
            except docker.errors.APIError as e:
                log.warning(f"Error stopping container: {e}")
            finally:
                self.container = None

    def restart_jenkins_service(self, timeout: int = 60) -> None:
        """
        Restart the Jenkins service without restarting the container.

        Args:
            timeout: Maximum time to wait for Jenkins to restart (seconds)
        """
        if not self.container:
            raise DockerJenkinsError("Container is not running")

        log.info("Restarting Jenkins service")
        try:
            result = self.container.exec_run("/usr/local/bin/restart-jenkins")
            if result.exit_code != 0:
                raise DockerJenkinsError(
                    f"Failed to restart Jenkins: {result.output.decode()}"
                )
        except docker.errors.APIError as e:
            raise DockerJenkinsError(f"Failed to execute restart command: {e}")

        # Wait for Jenkins to become ready again
        self.wait_for_ready(timeout)
        log.info("Jenkins service restarted successfully")

    def wait_for_ready(self, timeout: int = 300) -> None:
        """
        Wait for Jenkins to be ready to accept connections.

        Args:
            timeout: Maximum time to wait (seconds)
        """
        start_time = time.time()
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1))
        session.mount("http://", adapter)

        while time.time() - start_time < timeout:
            try:
                resp = session.get(f"{self.jenkins_url}/api/json", timeout=5)
                if resp.status_code == 200:
                    log.info("Jenkins is ready")
                    return
            except requests.RequestException as e:
                log.debug(f"Jenkins not ready yet: {e}")
            time.sleep(2)

        raise DockerJenkinsError(
            f"Jenkins did not become ready within {timeout} seconds"
        )

    def dump_plugin_versions(
        self, output_file: str = "plugin_versions.txt"
    ) -> str:
        """
        Dump installed plugin versions to a file.

        Args:
            output_file: Path to output file

        Returns:
            Path to the output file
        """
        if not self.container:
            raise DockerJenkinsError("Container is not running")

        log.info(f"Dumping plugin versions to {output_file}")
        try:
            result = self.container.exec_run(
                f"/usr/local/bin/dump-plugin-versions {output_file}"
            )
            if result.exit_code != 0:
                raise DockerJenkinsError(
                    f"Failed to dump plugin versions: {result.output.decode()}"
                )

            # Copy file from container
            bits, stat = self.container.get_archive(output_file)
            with open(output_file, "wb") as f:
                for chunk in bits:
                    f.write(chunk)

            log.info(f"Plugin versions dumped to {output_file}")
            return output_file
        except docker.errors.APIError as e:
            raise DockerJenkinsError(f"Failed to dump plugin versions: {e}")

    def get_logs(self, lines: int = 100) -> str:
        """Get container logs."""
        if not self.container:
            return ""
        return self.container.logs(tail=lines).decode()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
