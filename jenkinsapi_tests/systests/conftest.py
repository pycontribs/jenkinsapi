import os
import logging
import pytest
import time
import requests
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.jenkins_launcher import JenkinsLancher

log = logging.getLogger(__name__)


def pytest_collection_finish(session):
    """Check if systests are being collected after test collection is complete."""
    session._systests_collected = False
    for item in session.items:
        if "systests" in str(item.fspath):
            session._systests_collected = True
            log.info("Systests detected - will start Jenkins")
            break
    if not session._systests_collected:
        log.info("No systests detected - skipping Jenkins startup")


state = {}

# User/password for authentication testcases
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"

# Note: Plugins are now pre-installed in the Docker image
# See ci/plugins.txt for the list of included plugins


@pytest.fixture(scope="session")
def jenkins_launcher_mode():
    """Determine which Jenkins launcher mode will be used.

    Returns:
        dict: Information about the launcher mode
    """
    skip_docker = os.getenv("SKIP_DOCKER", "").lower() in ("1", "true")
    has_jenkins_url = "JENKINS_URL" in os.environ
    has_docker = JenkinsLancher._has_docker()

    if has_jenkins_url:
        mode = "external"
    elif skip_docker or not has_docker:
        mode = "war"
    else:
        mode = "docker"

    return {
        "mode": mode,
        "docker_available": has_docker,
        "skip_docker": skip_docker,
        "external_url": os.getenv("JENKINS_URL"),
        "docker_image": os.getenv(
            "JENKINS_DOCKER_IMAGE",
            "ghcr.io/pycontribs/jenkinsapi-jenkins:latest",
        ),
    }


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
def launched_jenkins(request, jenkins_launcher_mode):
    """Launch Jenkins instance for systests only."""
    # Skip if no systests are being collected
    if not getattr(request.session, "_systests_collected", False):
        pytest.skip("No systests to run")

    systests_dir, _ = os.path.split(__file__)
    local_orig_dir = os.path.join(systests_dir, "localinstance_files")
    if not os.path.exists(local_orig_dir):
        os.mkdir(local_orig_dir)
    launcher = JenkinsLancher(
        local_orig_dir,
        systests_dir,
        jenkins_url=os.getenv("JENKINS_URL", None),
    )

    # Log which method will be used for starting Jenkins
    mode = jenkins_launcher_mode["mode"]
    if mode == "external":
        log.info(
            "Using external Jenkins instance: %s",
            jenkins_launcher_mode["external_url"],
        )
    elif mode == "docker":
        log.info(
            "Starting Jenkins with Docker image: %s",
            jenkins_launcher_mode["docker_image"],
        )
    else:
        log.info(
            "Starting Jenkins with war file (Docker not available or disabled)"
        )

    launcher.start()

    # Store mode info on launcher for test access
    launcher.test_mode = mode
    launcher.test_config = jenkins_launcher_mode

    yield launcher

    log.info("All tests finished (mode: %s)", mode)
    launcher.stop()


@pytest.fixture(scope="session", autouse=True)
def cleanup_docker(request):
    """Cleanup Docker containers and images after all tests complete."""
    yield
    log.info("Running Docker cleanup after test session...")
    JenkinsLancher.cleanup_docker_images()


def ensure_jenkins_up(url, timeout=None):
    """Wait for Jenkins to be ready with exponential backoff.

    Checks frequently at first, then increases delay to reduce load.
    """
    # Default timeout is 180 seconds, but can be overridden
    # GitHub Actions runners may be slower, so we use a generous timeout
    if timeout is None:
        timeout = 180

    start = time.time()
    attempt = 0
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                log.info(
                    "Jenkins is ready after %.1f seconds", time.time() - start
                )
                return
        except Exception as err:
            log.debug("Jenkins not ready yet: %s", err)

        # Exponential backoff: 0.5s, 0.5s, 1s, 1s, 2s, 2s, etc.
        sleep_time = min(0.5 if attempt < 2 else 1 if attempt < 4 else 2, 2)
        time.sleep(sleep_time)
        attempt += 1

    pytest.exit("Jenkins didn't become available to call")


@pytest.fixture(scope="function")
def jenkins(launched_jenkins):
    url = launched_jenkins.jenkins_url

    jenkins_instance = Jenkins(url, timeout=60)
    ensure_jenkins_up(url)

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


@pytest.fixture(scope="function")
def executor_id(request):
    """Provide the executor ID for the current test.

    When running with pytest-xdist, this returns the worker ID (e.g., 'gw0', 'gw1').
    When running single-threaded, this returns 'local'.

    Tests can use this fixture to identify which executor/worker they're running on,
    allowing for dynamic executor assignment and load balancing.
    """
    # Check if running with pytest-xdist
    if hasattr(request.config, "workerinput"):
        worker_id = request.config.workerinput["workerid"]
    else:
        worker_id = "local"

    log.debug(f"Test '{request.node.name}' running on executor: {worker_id}")
    return worker_id
