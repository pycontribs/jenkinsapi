import os
import time
import shutil
import logging
import datetime
import tempfile

import docker
from docker.errors import DockerException, ImageNotFound, APIError

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.custom_exceptions import JenkinsAPIException

log = logging.getLogger(__name__)


class FailedToStart(Exception):
    pass


class TimeOut(Exception):
    pass


class JenkinsLancher:
    """
    Launch jenkins
    """

    def __init__(
        self,
        local_orig_dir,
        systests_dir,
        war_name=None,
        plugin_urls=None,
        jenkins_url=None,
    ):
        if jenkins_url is not None:
            self.jenkins_url = jenkins_url
            from urllib.parse import urlparse

            self.http_port = urlparse(jenkins_url).port
            self.start_new_instance = False
        else:
            # Use random port from environment or find available port
            jenkins_port = os.environ.get("JENKINS_PORT")
            if jenkins_port:
                self.http_port = int(jenkins_port)
            else:
                # Find an available port
                import socket

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(("127.0.0.1", 0))
                self.http_port = sock.getsockname()[1]
                sock.close()
            # Use 127.0.0.1 explicitly instead of localhost to avoid DNS issues
            self.jenkins_url = "http://127.0.0.1:%s" % self.http_port
            self.start_new_instance = True

        self.local_orig_dir = local_orig_dir
        self.systests_dir = systests_dir

        if "JENKINS_HOME" not in os.environ:
            self.jenkins_home = tempfile.mkdtemp(prefix="jenkins-home-")
            os.environ["JENKINS_HOME"] = self.jenkins_home
            # Make directory world-writable so Docker container can write to it.
            # Jenkins user inside container may have different UID than host.
            # This is necessary for mounted volumes to work properly in Docker.
            # noinspection PyUnresolvedReference
            os.chmod(self.jenkins_home, 0o777)  # nosec - necessary for Docker
        else:
            self.jenkins_home = os.environ["JENKINS_HOME"]

        self.docker_container_id = None

    @staticmethod
    def _has_docker():
        """Check if Docker is available on the system."""
        try:
            client = docker.from_env()
            client.ping()
            return True
        except (DockerException, Exception):
            return False

    @staticmethod
    def _check_docker_health():
        """Check if Docker daemon is healthy."""
        try:
            client = docker.from_env()
            client.ping()
            return True
        except Exception as e:
            log.warning("Docker health check failed: %s", e)
            return False

    def _ensure_docker_image(self, docker_image):
        """Ensure Docker image exists locally, pulling or building if necessary."""
        log.info("Checking for Docker image: %s", docker_image)
        client = docker.from_env()

        # Check if image exists locally
        try:
            client.images.get(docker_image)
            log.info("Docker image found locally: %s", docker_image)
            return
        except ImageNotFound:
            log.warning("Docker image not found locally")
        except Exception as e:
            log.warning("Error checking for image: %s", e)

        # Image not found, try to pull it
        log.info(
            "Image not found locally, attempting to pull: %s", docker_image
        )
        try:
            client.images.pull(docker_image)
            log.info("Successfully pulled image: %s", docker_image)
            return
        except APIError as e:
            log.warning(
                "Failed to pull image %s: %s",
                docker_image,
                str(e),
            )
        except DockerException as e:
            log.warning("Failed to pull image: %s", e)
        except Exception as e:
            log.warning("Failed to pull image: %s", e)

        # Pull failed or timed out, try to build from ci/Dockerfile
        log.info("Attempting to build Docker image from ci/Dockerfile")
        try:
            # Find the ci/Dockerfile relative to the project root
            ci_dir = self._find_ci_directory()
            if not ci_dir:
                raise FailedToStart(
                    "Cannot build image: ci/Dockerfile not found and image not available"
                )

            log.info("Building Docker image from: %s", ci_dir)
            client.images.build(path=ci_dir, tag=docker_image)
            log.info("Successfully built Docker image: %s", docker_image)
            return
        except DockerException as e:
            raise FailedToStart(f"Docker build failed: {e}")
        except Exception as e:
            raise FailedToStart(f"Docker build failed: {e}")

    def _find_ci_directory(self):
        """Find the ci/ directory containing the Dockerfile."""
        # Start from the location of this file and work upward
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Walk up the directory tree looking for ci/Dockerfile
        for _ in range(5):  # Look up to 5 levels
            ci_path = os.path.join(current_dir, "ci")
            dockerfile_path = os.path.join(ci_path, "Dockerfile")
            if os.path.isfile(dockerfile_path):
                return ci_path
            current_dir = os.path.dirname(current_dir)

        return None

    def _start_docker_jenkins(self, timeout):
        """Start Jenkins in a Docker container."""
        docker_image = os.environ.get(
            "JENKINS_DOCKER_IMAGE",
            "ghcr.io/pycontribs/jenkinsapi-jenkins:latest",
        )

        log.info("Starting Jenkins with Docker image: %s", docker_image)

        # Check Docker daemon health
        if not self._check_docker_health():
            log.warning(
                "Docker daemon may not be healthy, attempting anyway..."
            )

        # Ensure the Docker image is available (skip if SKIP_IMAGE_CHECK is set)
        if not os.environ.get("SKIP_IMAGE_CHECK"):
            self._ensure_docker_image(docker_image)

        # Wait a bit to ensure port is fully released from previous container
        time.sleep(2)

        # Run Docker container with performance optimizations
        java_opts = (
            "-Djenkins.install.runSetupWizard=false "
            "-Dhudson.DNSMultiCast.disabled=true "
            "-Dhudson.model.UpdateCenter.never=true "
            "-Djenkins.InitReactorRunner.concurrency=4 "
            "-XX:+TieredCompilation "
            "-XX:TieredStopAtLevel=4 "
            "-XX:+UseG1GC "
            "-Xms512m "
            "-Xmx1024m"
        )

        # Retry docker run with exponential backoff (OCI errors are transient)
        max_retries = 3
        retry_delay = 5
        last_error = None
        client = docker.from_env()

        for attempt in range(max_retries):
            try:
                log.info(
                    "Attempt %d/%d: Starting Jenkins Docker container...",
                    attempt + 1,
                    max_retries,
                )
                log.info(
                    "docker run -d -p 127.0.0.1:%s:8080 -v %s:/var/jenkins_home "
                    "-e JAVA_OPTS='...' %s",
                    self.http_port,
                    self.jenkins_home,
                    docker_image,
                )
                container = client.containers.run(
                    docker_image,
                    detach=True,
                    ports={"8080/tcp": ("127.0.0.1", self.http_port)},
                    volumes={
                        self.jenkins_home: {
                            "bind": "/var/jenkins_home",
                            "mode": "rw",
                        }
                    },
                    environment={"JAVA_OPTS": java_opts},
                )
                self.docker_container_id = container.id
                log.info(
                    "Jenkins container started with ID: %s",
                    self.docker_container_id,
                )
                break
            except APIError as e:
                last_error = str(e)
                log.error("Attempt %d failed: %s", attempt + 1, str(e))
                if attempt < max_retries - 1:
                    log.info("Retrying in %d seconds...", retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2
            except DockerException as e:
                last_error = str(e)
                log.error("Attempt %d failed: %s", attempt + 1, str(e))
                if attempt < max_retries - 1:
                    log.info("Retrying in %d seconds...", retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2
            except Exception as e:
                last_error = str(e)
                log.error("Attempt %d failed: %s", attempt + 1, str(e))
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
        else:
            # All retries failed
            raise FailedToStart(
                f"Docker run failed after {max_retries} attempts: {last_error}"
            )

        # Wait a moment for the container to fully initialize and bind ports
        log.info("Waiting for container to initialize...")
        time.sleep(5)

        # Wait for Jenkins to be ready
        self.block_until_jenkins_ready(timeout)

    def _stop_docker_jenkins(self):
        """Stop the Docker container."""
        if self.docker_container_id:
            log.info("Stopping Docker container: %s", self.docker_container_id)
            try:
                client = docker.from_env()
                container = client.containers.get(self.docker_container_id)
                container.stop(timeout=10)
                container.remove()
                log.info("Docker container stopped and removed.")
            except Exception as e:
                log.warning("Error stopping Docker container: %s", e)
            self.docker_container_id = None

    @staticmethod
    def cleanup_docker_images():
        """Clean up Jenkins Docker containers and images left from testing."""
        try:
            client = docker.from_env()
            log.info("Cleaning up Jenkins Docker containers...")

            # Find and remove containers based on jenkinsapi image
            containers = client.containers.list(
                all=True,
                filters={"ancestor": "ghcr.io/pycontribs/jenkinsapi-jenkins"},
            )
            for container in containers:
                try:
                    container.stop(timeout=5)
                    container.remove()
                    log.info("Removed container: %s", container.id[:12])
                except Exception as e:
                    log.warning(
                        "Failed to remove container %s: %s",
                        container.id[:12],
                        e,
                    )

            log.info("Jenkins Docker containers cleaned up.")
        except Exception as e:
            log.warning("Failed to cleanup Docker containers: %s", e)

    def stop(self):
        if self.start_new_instance:
            log.info("Shutting down jenkins.")

            # Clean up Docker container
            self._stop_docker_jenkins()

            # Do not remove jenkins home if JENKINS_URL is set
            if "JENKINS_URL" not in os.environ:
                shutil.rmtree(self.jenkins_home, ignore_errors=True)
            log.info("Jenkins stopped.")

    def block_until_jenkins_ready(self, timeout):
        start_time = datetime.datetime.now()
        timeout_time = start_time + datetime.timedelta(seconds=timeout)

        log.info(
            "Waiting for Jenkins to be ready at %s (timeout: %d seconds)",
            self.jenkins_url,
            timeout,
        )
        attempt = 1
        while True:
            try:
                # Use a shorter request timeout for health checks
                Jenkins(self.jenkins_url, timeout=5)
                log.info(
                    "Jenkins is finally ready for use after %d attempts.",
                    attempt,
                )
                return
            except Exception as e:
                if attempt % 6 == 0:  # Log container status every 30 seconds
                    self._log_container_status()
                log.info(
                    "Attempt %d: Jenkins is not yet ready (%s)",
                    attempt,
                    type(e).__name__,
                )
            if datetime.datetime.now() > timeout_time:
                # Log final container status before raising timeout
                self._log_container_status()
                raise TimeOut("Took too long for Jenkins to become ready...")
            time.sleep(5)
            attempt += 1

    def _log_container_status(self):
        """Log Docker container status and recent logs for debugging."""
        if not self.docker_container_id:
            return

        try:
            client = docker.from_env()
            container = client.containers.get(self.docker_container_id)

            # Log container state
            container.reload()
            log.warning("Container state: %s", container.status)

            # Get and log recent container logs
            logs = container.logs(tail=50, decode=True)
            log.warning("Recent container logs:\n%s", logs)
        except Exception as e:
            log.warning("Failed to get container status: %s", e)

    def start(self, timeout=180):
        if self.start_new_instance:
            self.jenkins_home = os.environ.get(
                "JENKINS_HOME", self.jenkins_home
            )

            # Docker is the only method for starting new instances
            log.info("Starting Jenkins with Docker")
            self._start_docker_jenkins(timeout)


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.INFO)

    log.info("Hello!")

    utils_dir = os.path.dirname(os.path.abspath(__file__))  # jenkinsapi/utils
    jenkinsapi_tests_path = os.path.join(
        utils_dir, "..", "..", "jenkinsapi_tests"
    )
    systests_jenkinsapi_tests_path = os.path.join(
        jenkinsapi_tests_path, "systests"
    )
    localinstance_files_path = os.path.join(
        systests_jenkinsapi_tests_path, "localinstance_files"
    )
    jl = JenkinsLancher(
        localinstance_files_path,
        systests_jenkinsapi_tests_path,
        "jenkins.war",
    )

    jl.start()
    log.info("Jenkins was launched...")

    time.sleep(10)

    log.info("...now to shut it down!")
    jl.stop()
