"""
System tests for API token revocation.
"""

import logging
import pytest
from jenkinsapi.utils.crumb_requester import CrumbRequester

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def test_revoke_api_token(jenkins_admin_admin):
    jenkins_admin_admin.requester = CrumbRequester(
        baseurl=jenkins_admin_admin.baseurl,
        username=jenkins_admin_admin.username,
        password=jenkins_admin_admin.password,
    )
    jenkins_admin_admin.poll()

    jenkins_admin_admin.generate_new_api_token("token-to-revoke")

    url = (
        "%s/me/descriptorByName/jenkins.security.ApiTokenProperty/api/json"
        % jenkins_admin_admin.baseurl
    )
    resp = jenkins_admin_admin.requester.get_url(url)
    token_list = resp.json().get("tokenList", [])
    assert len(token_list) >= 1

    token_uuid = token_list[-1]["uuid"]
    jenkins_admin_admin.revoke_api_token(token_uuid)

    resp = jenkins_admin_admin.requester.get_url(url)
    remaining = [t["uuid"] for t in resp.json().get("tokenList", [])]
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

    jenkins_admin_admin.revoke_all_api_tokens()

    url = (
        "%s/me/descriptorByName/jenkins.security.ApiTokenProperty/api/json"
        % jenkins_admin_admin.baseurl
    )
    resp = jenkins_admin_admin.requester.get_url(url)
    assert resp.json().get("tokenList", []) == []
