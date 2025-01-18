"""
System tests for generation new api token for logged in user
"""

import pytest
import logging
from jenkinsapi.utils.crumb_requester import CrumbRequester


log = logging.getLogger(__name__)


@pytest.mark.generate_new_api_token
def test_generate_new_api_token(jenkins_admin_admin):
    jenkins_admin_admin.requester = CrumbRequester(
        baseurl=jenkins_admin_admin.baseurl,
        username=jenkins_admin_admin.username,
        password=jenkins_admin_admin.password,
    )
    jenkins_admin_admin.poll()

    new_token = (
        jenkins_admin_admin.generate_new_api_token()
    )  # generate new token
    log.info("newly generated token: %s", new_token)
    assert new_token is not None
