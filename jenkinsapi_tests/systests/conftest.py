import os
import logging
import pytest
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.jenkins_launcher import JenkinsLancher

log = logging.getLogger(__name__)
state = {}

# User/password for authentication testcases
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"

# Extra plugins required by the systests
PLUGIN_DEPENDENCIES = [
    "https://updates.jenkins.io/latest/"
    "https://updates.jenkins.io/latest/mina-sshd-api-core.hpi",
    "https://updates.jenkins.io/latest/mina-sshd-api-common.hpi",
    "apache-httpcomponents-client-4-api.hpi",
    "https://updates.jenkins.io/latest/jsch.hpi",
    "https://updates.jenkins.io/latest/gson-api.hpi",
    "https://updates.jenkins.io/latest/trilead-api.hpi",
    "https://updates.jenkins.io/latest/bouncycastle-api.hpi",
    "https://updates.jenkins.io/latest/ssh-slaves.hpi",
    "https://updates.jenkins.io/latest/instance-identity.hpi",
    "https://updates.jenkins.io/download/plugins/bootstrap5-api/5.3.3-2/bootstrap5-api.hpi",
    "https://updates.jenkins.io/latest/workflow-api.hpi",
    "https://updates.jenkins.io/latest/display-url-api.hpi",
    "https://updates.jenkins.io/latest/eddsa-api.hpi",
    "https://updates.jenkins.io/latest/workflow-step-api.hpi",
    "https://updates.jenkins.io/latest/workflow-scm-step.hpi",
    "https://updates.jenkins.io/latest/junit.hpi",
    "https://updates.jenkins.io/latest/script-security.hpi",
    "https://updates.jenkins.io/latest/matrix-project.hpi",
    "https://updates.jenkins.io/latest/credentials.hpi",
    "https://updates.jenkins.io/latest/variant.hpi",
    "https://updates.jenkins.io/latest/ssh-credentials.hpi",
    "https://updates.jenkins.io/latest/asm-api.hpi",
    "https://updates.jenkins.io/latest/scm-api.hpi",
    "https://updates.jenkins.io/latest/git.hpi",
    "https://updates.jenkins.io/latest/git-client.hpi",
    "https://updates.jenkins.io/latest/jakarta-mail-api.hpi",
    "https://updates.jenkins.io/latest/nested-view.hpi",
    "https://updates.jenkins.io/latest/structs.hpi",
    "https://updates.jenkins.io/latest/plain-credentials.hpi",
    "https://updates.jenkins.io/latest/envinject.hpi",
    "https://updates.jenkins.io/latest/envinject-api.hpi",
    "https://updates.jenkins.io/latest/jdk-tool.hpi",
    "https://updates.jenkins.io/latest/credentials-binding.hpi",
    "https://updates.jenkins.io/latest/jakarta-activation-api.hpi",
    "https://updates.jenkins.io/latest/caffeine-api.hpi",
    "https://updates.jenkins.io/latest/script-security.hpi",
    "https://updates.jenkins.io/latest/checks-api.hpi",
    "https://updates.jenkins.io/latest/json-api.hpi",
    "https://updates.jenkins.io/latest/jackson2-api.hpi",
    "https://updates.jenkins.io/latest/echarts-api.hpi",
    "https://updates.jenkins.io/latest/ionicons-api.hpi",
    "https://updates.jenkins.io/latest/plugin-util-api.hpi",
    "https://updates.jenkins.io/latest/font-awesome-api.hpi",
    "https://updates.jenkins.io/latest/popper2-api.hpi",
    "https://updates.jenkins.io/latest/commons-text-api.hpi",
    "https://updates.jenkins.io/latest/commons-lang3-api.hpi",
    "https://updates.jenkins.io/latest/plugin-util-api.hpi",
    "https://updates.jenkins.io/latest/snakeyaml-api.hpi",
    "https://updates.jenkins.io/latest/workflow-support.hpi",
    "https://updates.jenkins.io/latest/jquery3-api.hpi",
    "https://updates.jenkins.io/latest/checks-api.hpi",
    "https://updates.jenkins.io/latest/javax-activation-api.hpi",
    "https://updates.jenkins.io/latest/jaxb.hpi",
    "https://updates.jenkins.io/latest/instance-identity.hpi",
    "https://updates.jenkins.io/latest/mailer.hpi",
]


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
    """.format(
        ADMIN_USER, ADMIN_PASSWORD
    )

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
    launcher = JenkinsLancher(
        local_orig_dir,
        systests_dir,
        war_name,
        PLUGIN_DEPENDENCIES,
        jenkins_url=os.getenv("JENKINS_URL", None),
    )
    launcher.start()

    yield launcher

    log.info("All tests finished")
    launcher.stop()


@pytest.fixture(scope="function")
def jenkins(launched_jenkins):
    url = launched_jenkins.jenkins_url

    jenkins_instance = Jenkins(url, timeout=30)

    _delete_all_jobs(jenkins_instance)
    _delete_all_views(jenkins_instance)
    _delete_all_credentials(jenkins_instance)

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
def jenkins_admin_admin(
    launched_jenkins, jenkins
):  # pylint: disable=unused-argument
    # Using "jenkins" fixture makes sure that jobs/views/credentials are
    # cleaned before security is enabled.
    url = launched_jenkins.jenkins_url

    _create_admin_user(launched_jenkins)
    jenkins_admin_instance = Jenkins(url, ADMIN_USER, ADMIN_PASSWORD)

    yield jenkins_admin_instance

    jenkins_admin_instance.requester.__class__.AUTH_COOKIE = None
    _disable_security(launched_jenkins)
