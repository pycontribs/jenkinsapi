"""Docker-based Jenkins instance manager for testing."""

import io
import logging
import os
import tarfile
import time
from typing import Optional

import docker
import requests

log = logging.getLogger(__name__)


DEFAULT_IMAGE_NAME = "jenkinsapi-systest:latest"
DEFAULT_CONTAINER_NAME = "jenkinsapi-systest"


class DockerJenkinsError(Exception):
    """Raised when Docker-backed Jenkins setup or control fails."""


class DockerJenkins:
    """Manage a Jenkins instance running in Docker."""

    def __init__(
        self,
        image_name: str = DEFAULT_IMAGE_NAME,
        container_name: str = DEFAULT_CONTAINER_NAME,
        port: int = 8080,
        jenkins_home: Optional[str] = None,
    ):
        self.image_name = image_name
        self.container_name = container_name
        self.port = port
        self.jenkins_home = jenkins_home
        self.client = docker.from_env()
        self.container = None
        self.jenkins_url = f"http://localhost:{port}"

    def build_image(self, dockerfile_path: str = "docker/Dockerfile") -> None:
        try:
            self.client.images.get(self.image_name)
            log.info(
                "Image %s already exists, skipping build", self.image_name
            )
            return
        except docker.errors.ImageNotFound:
            pass

        if not os.path.exists(dockerfile_path):
            raise DockerJenkinsError(
                f"Dockerfile not found: {dockerfile_path}"
            )

        log.info("Building image %s from %s", self.image_name, dockerfile_path)
        try:
            self.client.images.build(
                path=os.path.dirname(os.path.abspath(dockerfile_path)),
                dockerfile=os.path.basename(dockerfile_path),
                tag=self.image_name,
                rm=True,
            )
        except (docker.errors.BuildError, docker.errors.APIError) as e:
            raise DockerJenkinsError(f"Failed to build image: {e}")

    def start(self, timeout: int = 300) -> None:
        self._remove_existing_container()

        volumes = {}
        if self.jenkins_home:
            volumes = {
                self.jenkins_home: {"bind": "/var/jenkins_home", "mode": "rw"}
            }

        try:
            self.container = self.client.containers.run(
                self.image_name,
                name=self.container_name,
                ports={"8080/tcp": self.port},
                volumes=volumes,
                detach=True,
                remove=False,
            )
        except docker.errors.ImageNotFound:
            raise DockerJenkinsError(
                f"Image not found: {self.image_name}. Build it first."
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

        self.wait_for_ready(timeout)

    def _remove_existing_container(self) -> None:
        try:
            existing = self.client.containers.get(self.container_name)
        except docker.errors.NotFound:
            return

        existing.stop()
        existing.remove()

    def stop(self) -> None:
        if self.container:
            try:
                self.container.stop(timeout=10)
                self.container.remove()
            except docker.errors.NotFound:
                pass  # container already removed
            except docker.errors.APIError as e:
                log.warning("Error stopping container: %s", e)
            finally:
                self.container = None

    def restart_jenkins_service(self, timeout: int = 60) -> None:
        if not self.container:
            raise DockerJenkinsError("Container is not running")

        result = self.container.exec_run("/usr/local/bin/restart-jenkins")
        if result.exit_code != 0:
            raise DockerJenkinsError(
                f"Failed to restart Jenkins: {result.output.decode()}"
            )

        self.wait_for_ready(timeout)

    def wait_for_ready(self, timeout: int = 300) -> None:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                resp = requests.get(f"{self.jenkins_url}/api/json", timeout=5)
                if resp.status_code == 200:
                    return
            except requests.RequestException:
                pass
            time.sleep(2)

        raise DockerJenkinsError(
            f"Jenkins did not become ready within {timeout} seconds"
        )

    def dump_plugin_versions(
        self, output_file: str = "plugin_versions.txt"
    ) -> str:
        if not self.container:
            raise DockerJenkinsError("Container is not running")

        archive_name = os.path.basename(output_file)
        result = self.container.exec_run(
            f"/usr/local/bin/dump-plugin-versions {archive_name}"
        )
        if result.exit_code != 0:
            raise DockerJenkinsError(
                f"Failed to dump plugin versions: {result.output.decode()}"
            )

        bits, _ = self.container.get_archive(archive_name)
        archive_bytes = b"".join(bits)
        with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as archive:
            member = archive.getmember(archive_name)
            extracted = archive.extractfile(member)
            if extracted is None:
                raise DockerJenkinsError(
                    f"Failed to extract plugin versions: {archive_name}"
                )
            with open(output_file, "wb") as f:
                f.write(extracted.read())

        return output_file

    def get_logs(self, lines: int = 100) -> str:
        if not self.container:
            return ""
        return self.container.logs(tail=lines).decode(errors="replace")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
