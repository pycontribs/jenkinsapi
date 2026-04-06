import os
import logging
import pytest
import time
import requests
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.docker_jenkins import DockerJenkins, DEFAULT_IMAGE_NAME
from jenkinsapi_tests.unittests.conftest_helpers import (
    parse_worker_id,
    generate_container_name,
    find_free_port,
)

log = logging.getLogger(__name__)
state = {}

# User/password for authentication testcases
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"


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
    dockerfile_path = os.path.join(repo_root, "docker", "Dockerfile")

    client = docker_lib.from_env()
    image_name = DEFAULT_IMAGE_NAME

    # If image already exists, all workers can use it immediately
    try:
        client.images.get(image_name)
        log.info(
            "[%s] Docker image already exists, skipping build", display_name
        )
        return image_name
    except docker_lib.errors.ImageNotFound:
        pass

    if worker_num == 0:
        log.info("[%s] Building Docker image %s...", display_name, image_name)
        try:
            client.images.build(
                path=os.path.dirname(dockerfile_path),
                dockerfile="Dockerfile",
                tag=image_name,
                rm=True,
            )
            log.info("[%s] Image build complete", display_name)
            return image_name
        except Exception as e:
            log.error("[%s] Image build failed: %s", display_name, e)
            raise
    log.info(
        "[%s] Waiting for shared image to be built by worker-0...",
        display_name,
    )
    max_wait = 300
    start = time.time()
    while time.time() - start < max_wait:
        try:
            client.images.get(image_name)
            log.info("[%s] Image ready", display_name)
            return image_name
        except docker_lib.errors.ImageNotFound:
            time.sleep(2)
    raise RuntimeError(f"Timeout waiting for image (waited {max_wait}s)")


@pytest.fixture(scope="session")
def launched_jenkins(docker_image, worker_id):
    worker_num, display_name = parse_worker_id(worker_id)
    base_port = 8080 if worker_num == 0 else 8100 + (worker_num - 1) * 10
    port = find_free_port(start_port=base_port)
    container_name = generate_container_name(
        worker_id, base_name="jenkinsapi-systest"
    )

    launcher = DockerJenkins(
        image_name=docker_image,
        container_name=container_name,
        port=port,
    )

    log.info(
        "[%s] Starting container %s on port %d",
        display_name,
        container_name,
        port,
    )
    launcher.start(timeout=300)
    ensure_jenkins_up(launcher.jenkins_url, timeout=60)

    yield launcher

    log.info("[%s] All tests finished", display_name)
    launcher.stop()


def ensure_jenkins_up(url, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{url}/api/json", timeout=5)
            if resp.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(2)
    pytest.exit("Jenkins didn't become available to call")


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
