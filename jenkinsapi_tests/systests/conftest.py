import atexit
import os
import signal
import sys
import logging
import pytest
import time
import queue
import requests
from pathlib import Path
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.docker_jenkins import DockerJenkinsError
from jenkinsapi.utils.docker_launcher import DockerLauncher

# Import helpers for dynamic port allocation
sys.path.insert(0, str(Path(__file__).parent.parent / "unittests"))
from conftest_helpers import (
    parse_worker_id,
    generate_container_name,
    find_free_port,
)

pytestmark = pytest.mark.docker

log = logging.getLogger(__name__)
state = {}

# Container pool management
CONTAINER_POOLS = {}  # Maps worker_id -> queue of available containers
CONTAINER_LAUNCHERS = {}  # Maps (worker_id, container_num) -> launcher

# User/password for authentication testcases
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"


def _emergency_cleanup():
    for launcher in CONTAINER_LAUNCHERS.values():
        try:
            launcher.stop()
        except Exception:
            pass


atexit.register(_emergency_cleanup)
signal.signal(signal.SIGTERM, lambda *_: (_emergency_cleanup(), sys.exit(1)))


def _delete_all_jobs(jenkins):
    jenkins.poll()
    for name in jenkins.keys():
        del jenkins[name]


def _delete_all_views(jenkins):
    all_view_names = jenkins.views.keys()[1:]
    for name in all_view_names:
        del jenkins.views[name]


def _delete_all_credentials(jenkins):
    all_cred_names = jenkins.credentials.keys()
    for name in all_cred_names:
        del jenkins.credentials[name]


def _create_admin_user(launched_jenkins):
    # Groovy script that creates a user "admin/admin" in jenkins
    # and enable security. "admin" user will be the only user and
    # have admin permissions. Anonymous cannot read anything.
    create_admin_groovy = """
import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()

def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount('{0}','{1}')
instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)
    """.format(ADMIN_USER, ADMIN_PASSWORD)

    url = launched_jenkins.jenkins_url
    jenkins_instance = Jenkins(url)
    jenkins_instance.run_groovy_script(create_admin_groovy)


def _disable_security(launched_jenkins):
    # Groovy script that disables security in jenkins,
    # reverting the changes made in "_create_admin_user" function.
    disable_security_groovy = """
import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()
instance.disableSecurity()
instance.save()
    """

    url = launched_jenkins.jenkins_url
    jenkins_instance = Jenkins(url, ADMIN_USER, ADMIN_PASSWORD)
    jenkins_instance.run_groovy_script(disable_security_groovy)


@pytest.fixture(scope="session")
def docker_image(worker_id):
    """
    Build shared Docker image once per session.

    Worker 0 builds the image; all other workers wait for it.
    All workers share one image but each gets a unique container.
    """
    import docker as docker_lib

    worker_num, display_name = parse_worker_id(worker_id)
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    dockerfile_path = os.path.join(repo_root, "Dockerfile")

    client = docker_lib.from_env()
    image_name = "jenkinsapi-systest:latest"

    # If image already exists, all workers can use it immediately
    try:
        client.images.get(image_name)
        log.info(
            f"[{display_name}] Docker image already exists, skipping build"
        )
        yield image_name
        return
    except docker_lib.errors.ImageNotFound:
        pass

    if worker_num == 0:
        log.info(f"[{display_name}] Building Docker image {image_name}...")
        try:
            client.images.build(
                path=os.path.dirname(dockerfile_path),
                dockerfile="Dockerfile",
                tag=image_name,
                rm=True,
            )
            log.info(f"[{display_name}] Image build complete")
            yield image_name
        except Exception as e:
            log.error(f"[{display_name}] Image build failed: {e}")
            raise
    else:
        # Wait for worker 0 to finish building the shared image
        log.info(
            f"[{display_name}] Waiting for shared image to be built by worker-0..."
        )
        max_wait = 300
        start = time.time()
        while time.time() - start < max_wait:
            try:
                client.images.get(image_name)
                log.info(f"[{display_name}] Image ready")
                yield image_name
                return
            except docker_lib.errors.ImageNotFound:
                time.sleep(2)
        raise RuntimeError(f"Timeout waiting for image (waited {max_wait}s)")


@pytest.fixture(scope="session", autouse=True)
def container_pool(docker_image, worker_id):
    """
    Create a single Docker container per xdist worker.

    Each worker independently manages its own container.
    Tests get the container from the pool, use it, and return it for reuse.
    Image name is unique per worker to avoid conflicts.
    """
    worker_num, display_name = parse_worker_id(worker_id)
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    dockerfile_path = os.path.join(repo_root, "Dockerfile")

    # docker_image fixture now returns the unique image name
    image_name = docker_image

    pool = queue.Queue()
    launchers = []
    num_containers = 1

    log.info(f"[{display_name}] Starting Docker container for xdist worker...")

    try:
        for container_num in range(num_containers):
            # Calculate unique port for this worker
            # worker-0: 8080, worker-1: 8100, worker-2: 8200, etc.
            if worker_num == 0:
                port = 8080
            else:
                port = 8000 + (worker_num * 100)

            # Ensure port is actually free
            port = find_free_port(start_port=port)
            container_name = f"jenkinsapi-systest-{display_name}"

            log.info(
                f"[{display_name}] Starting container {container_name} on port {port} "
                f"using image {image_name}"
            )

            for attempt in range(5):
                try:
                    launcher = DockerLauncher(
                        image_name=image_name,
                        container_name=container_name,
                        port=port,
                        dockerfile_path=dockerfile_path,
                        jenkins_url=os.getenv("JENKINS_URL", None),
                    )
                    launcher.start(timeout=300)
                    break
                except DockerJenkinsError as e:
                    if attempt == 4 or "Port conflict" not in str(e):
                        raise
                    port = find_free_port(start_port=port + 1)
                    log.warning(
                        f"[{display_name}] Port conflict, retrying on port {port}: {e}"
                    )

            # Ensure Jenkins is fully ready before marking container as ready
            log.info(
                f"[{display_name}] Verifying Jenkins is fully responsive..."
            )
            ensure_jenkins_up(launcher.jenkins_url, timeout=60)

            launchers.append(launcher)
            pool.put(launcher)

        log.info(
            f"[{display_name}] Container fully ready for testing, "
            f"all {num_containers} instance(s) verified"
        )

        # Store in global dict for cleanup
        CONTAINER_POOLS[worker_id] = pool
        for i, launcher in enumerate(launchers):
            CONTAINER_LAUNCHERS[(worker_id, i)] = launcher

        yield pool
    finally:
        # Cleanup all containers in the pool
        log.info(f"[{display_name}] Cleaning up container pool...")
        for launcher in launchers:
            try:
                launcher.stop()
            except Exception as e:
                log.warning(f"[{display_name}] Error stopping container: {e}")


@pytest.fixture(scope="function")
def launched_jenkins(container_pool, worker_id):
    """
    Get a Docker instance from the worker's container pool.

    Tests use containers from the pool, which are reused across tests.
    """
    worker_num, display_name = parse_worker_id(worker_id)

    # Get container from pool (wait up to 60 seconds)
    try:
        launcher = container_pool.get(timeout=60)
        log.info(
            f"[{display_name}] Acquired container from pool: {launcher.jenkins_url}"
        )
    except queue.Empty:
        pytest.fail(
            f"[{display_name}] No containers available in pool after 60 seconds"
        )

    yield launcher

    # Return container to pool for reuse
    try:
        # Clean up test artifacts before returning to pool
        jenkins_instance = Jenkins(launcher.jenkins_url, timeout=30)
        _delete_all_jobs(jenkins_instance)
        _delete_all_views(jenkins_instance)
        _delete_all_credentials(jenkins_instance)
    except Exception as e:
        log.warning(
            f"[{display_name}] Error cleaning up after test: {e}. "
            "Returning container to pool anyway."
        )

    container_pool.put(launcher)
    log.info(f"[{display_name}] Returned container to pool")


def ensure_jenkins_up(url, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return
        except Exception as err:
            print("Exception connecting to jenkins", err)
        time.sleep(2)
    pytest.exit("Jenkins didnt become available to call")


@pytest.fixture(scope="function")
def jenkins(launched_jenkins):
    url = launched_jenkins.jenkins_url

    jenkins_instance = Jenkins(url, timeout=60)
    ensure_jenkins_up(url, timeout=60)

    # Retry cleanup operations to handle transient connection issues
    max_retries = 3
    for attempt in range(max_retries):
        try:
            _delete_all_jobs(jenkins_instance)
            _delete_all_views(jenkins_instance)
            _delete_all_credentials(jenkins_instance)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                log.warning(
                    f"Cleanup attempt {attempt + 1} failed, retrying: {e}"
                )
                time.sleep(2)

    return jenkins_instance


@pytest.fixture(scope="function")
def lazy_jenkins(launched_jenkins):
    url = launched_jenkins.jenkins_url

    jenkins_instance = Jenkins(url, lazy=True)

    _delete_all_jobs(jenkins_instance)
    _delete_all_views(jenkins_instance)
    _delete_all_credentials(jenkins_instance)

    return jenkins_instance


@pytest.fixture(scope="function")
def jenkins_admin_admin(launched_jenkins, jenkins):  # pylint: disable=unused-argument
    # Using "jenkins" fixture makes sure that jobs/views/credentials are
    # cleaned before security is enabled.
    url = launched_jenkins.jenkins_url

    _create_admin_user(launched_jenkins)
    jenkins_admin_instance = Jenkins(url, ADMIN_USER, ADMIN_PASSWORD)

    yield jenkins_admin_instance

    jenkins_admin_instance.requester.__class__.AUTH_COOKIE = None
    _disable_security(launched_jenkins)
