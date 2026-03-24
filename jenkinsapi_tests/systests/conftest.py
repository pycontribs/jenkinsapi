import os
import logging
import pytest
import time
import requests
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.jenkins_launcher import JenkinsLancher

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
def launched_jenkins():
    systests_dir, _ = os.path.split(__file__)
    local_orig_dir = os.path.join(systests_dir, "localinstance_files")
    if not os.path.exists(local_orig_dir):
        os.mkdir(local_orig_dir)
    war_name = "jenkins.war"
    plugins_txt = os.path.join(systests_dir, "plugins.txt")
    launcher = JenkinsLancher(
        local_orig_dir,
        systests_dir,
        war_name,
        plugins_txt=plugins_txt,
        jenkins_url=os.getenv("JENKINS_URL", None),
    )
    launcher.start()

    yield launcher

    log.info("All tests finished")
    launcher.stop()


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
