"""
System tests for Jenkins user management (create/delete).
"""

import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def test_create_and_delete_user(jenkins_admin_admin):
    username = "testuser_%s" % random_string(6)
    jenkins_admin_admin.create_user(
        username, "password123", "Test User", "%s@example.com" % username
    )

    url = "%s/user/%s/api/json" % (jenkins_admin_admin.baseurl, username)
    resp = jenkins_admin_admin.requester.get_url(url)
    assert resp.status_code == 200

    jenkins_admin_admin.delete_user(username)

    resp = jenkins_admin_admin.requester.get_url(
        url, params={}, valid=[404, 200]
    )
    assert resp.status_code == 404
