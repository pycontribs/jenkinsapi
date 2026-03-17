import io
import time
import json
import logging
import pytest

from urllib.parse import urljoin
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.crumb_requester import CrumbRequester
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import JOB_WITH_FILE


log = logging.getLogger(__name__)

DEFAULT_JENKINS_PORT = 8080

ENABLE_CRUMBS_CONFIG = {
    "hudson-security-csrf-GlobalCrumbIssuerConfiguration": {
        "csrf": {
            "issuer": {
                "value": "0",
                "stapler-class": "hudson.security.csrf.DefaultCrumbIssuer",
                "$class": "hudson.security.csrf.DefaultCrumbIssuer",
                "excludeClientIPFromCrumb": False,
            }
        }
    }
}

DISABLE_CRUMBS_CONFIG = {
    "hudson-security-csrf-GlobalCrumbIssuerConfiguration": {},
}

SECURITY_SETTINGS = {
    "": "0",
    "markupFormatter": {
        "stapler-class": "hudson.markup.EscapedMarkupFormatter",
        "$class": "hudson.markup.EscapedMarkupFormatter",
    },
    "org-jenkinsci-main-modules-sshd-SSHD": {
        "port": {"value": "", "type": "disabled"}
    },
    "jenkins-CLI": {"enabled": False},
    # This is not required if envinject plugin is not installed
    # but since it is installed for test suite - we must have this config
    # If this is not present - Jenkins will return error
    "org-jenkinsci-plugins-envinject-EnvInjectPluginConfiguration": {
        "enablePermissions": False,
        "hideInjectedVars": False,
        "enableLoadingFromMaster": False,
    },
    "jenkins-model-DownloadSettings": {"useBrowser": False},
    "slaveAgentPort": {"value": "", "type": "disable"},
    "agentProtocol": [
        "CLI-connect",
        "CLI2-connect",
        "JNLP-connect",
        "JNLP2-connect",
        "JNLP4-connect",
    ],
    "core:apply": "",
}


@pytest.fixture(scope="function")
def crumbed_jenkins(jenkins):
    ENABLE_CRUMBS_CONFIG.update(SECURITY_SETTINGS)
    DISABLE_CRUMBS_CONFIG.update(SECURITY_SETTINGS)

    jenkins.requester.post_and_confirm_status(
        urljoin(jenkins.baseurl, "/configureSecurity/configure"),
        data={"Submit": "save", "json": json.dumps(ENABLE_CRUMBS_CONFIG)},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    log.info("Enabled Jenkins security")

    crumbed = Jenkins(
        jenkins.baseurl, requester=CrumbRequester(baseurl=jenkins.baseurl)
    )

    yield crumbed

    crumbed.requester.post_and_confirm_status(
        jenkins.baseurl + "/configureSecurity/configure",
        data={"Submit": "save", "json": json.dumps(DISABLE_CRUMBS_CONFIG)},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    log.info("Disabled Jenkins security")


def test_invoke_job_with_file(crumbed_jenkins):
    # Retry with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            file_data = random_string()
            param_file = io.BytesIO(file_data.encode("utf-8"))

            job_name = "create1_%s" % random_string()
            job = crumbed_jenkins.create_job(job_name, JOB_WITH_FILE)

            assert job.has_params()
            assert len(job.get_params_list())

            job.invoke(block=True, files={"file.txt": param_file})

            build = job.get_last_build()
            while build.is_running():
                time.sleep(0.25)

            artifacts = build.get_artifact_dict()
            assert isinstance(artifacts, dict) is True
            art_file = artifacts["file.txt"]
            assert art_file.get_data().decode("utf-8").strip() == file_data
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error
