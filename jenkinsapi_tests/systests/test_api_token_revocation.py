"""
System tests for API token revocation.
"""

import logging
import json
import pytest
from jenkinsapi.utils.crumb_requester import CrumbRequester

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def _get_token_uuids(jenkins):
    script = """
import groovy.json.JsonOutput
import hudson.model.User
import jenkins.security.ApiTokenProperty

def user = User.current()
def property = user.getProperty(ApiTokenProperty)
def token_list = property.tokenStore.tokenList.collect { token ->
    [uuid: token.uuid]
}
println(JsonOutput.toJson(token_list))
""".strip()
    return [
        token["uuid"]
        for token in json.loads(jenkins.run_groovy_script(script))
    ]


def test_revoke_api_token(jenkins_admin_admin):
    jenkins_admin_admin.requester = CrumbRequester(
        baseurl=jenkins_admin_admin.baseurl,
        username=jenkins_admin_admin.username,
        password=jenkins_admin_admin.password,
    )
    jenkins_admin_admin.poll()

    jenkins_admin_admin.generate_new_api_token("token-to-revoke")
    token_uuids = _get_token_uuids(jenkins_admin_admin)
    assert token_uuids

    token_uuid = token_uuids[-1]
    jenkins_admin_admin.revoke_api_token(token_uuid)
    remaining = _get_token_uuids(jenkins_admin_admin)
    assert token_uuid not in remaining


def test_revoke_all_api_tokens(jenkins_admin_admin):
    jenkins_admin_admin.requester = CrumbRequester(
        baseurl=jenkins_admin_admin.baseurl,
        username=jenkins_admin_admin.username,
        password=jenkins_admin_admin.password,
    )
    jenkins_admin_admin.poll()

    jenkins_admin_admin.generate_new_api_token("token-1")
    jenkins_admin_admin.generate_new_api_token("token-2")

    assert _get_token_uuids(jenkins_admin_admin)
    jenkins_admin_admin.revoke_all_api_tokens()
    assert _get_token_uuids(jenkins_admin_admin) == []
