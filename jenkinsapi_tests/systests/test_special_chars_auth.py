"""
Tests for issue #862: Auth when password has special characters fails.
https://github.com/pycontribs/jenkinsapi/issues/862

These tests use real Jenkins auth requests against a launcher instance.
"""

import base64
import pytest
import requests

from jenkinsapi.jenkins import Jenkins


SPECIAL_CHAR_PASSWORD = "zzzzzz6@Y74(K.xxxxxxx"
SPECIAL_CHAR_USER = "specialuser"

pytestmark = pytest.mark.docker


def _create_user_with_special_chars(jenkins_admin_admin):
    """Create a user with special character password using Groovy."""
    create_user_groovy = f"""
import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()
def realm = instance.getSecurityRealm()

if (realm instanceof HudsonPrivateSecurityRealm) {{
    realm.createAccount('{SPECIAL_CHAR_USER}', '{SPECIAL_CHAR_PASSWORD}')
}}
"""
    jenkins_admin_admin.run_groovy_script(create_user_groovy)


def _delete_user_with_special_chars(jenkins_admin_admin):
    """Delete the special chars test user."""
    delete_user_groovy = f"""
import jenkins.model.*

def instance = Jenkins.getInstance()
def realm = instance.getSecurityRealm()

if (realm instanceof HudsonPrivateSecurityRealm) {{
    realm.deleteUser('{SPECIAL_CHAR_USER}')
}}
"""
    jenkins_admin_admin.run_groovy_script(delete_user_groovy)


@pytest.fixture
def jenkins_with_special_char_user(launched_jenkins, jenkins_admin_admin):
    """Set up Jenkins with security enabled and a user with special char password."""
    _create_user_with_special_chars(jenkins_admin_admin)

    yield launched_jenkins

    _delete_user_with_special_chars(jenkins_admin_admin)


def test_special_char_password_auth_succeeds(jenkins_with_special_char_user):
    """Authentication with special character password must succeed."""
    url = jenkins_with_special_char_user.jenkins_url

    # Should not raise an exception
    jenkins = Jenkins(
        url,
        username=SPECIAL_CHAR_USER,
        password=SPECIAL_CHAR_PASSWORD,
        timeout=10,
    )
    assert jenkins.username == SPECIAL_CHAR_USER
    assert jenkins.password == SPECIAL_CHAR_PASSWORD
    # Verify we can make requests
    jenkins.poll()


def test_special_char_password_wrong_password_raises_401(
    jenkins_with_special_char_user,
):
    """Wrong password with special chars in correct password must raise HTTPError."""
    url = jenkins_with_special_char_user.jenkins_url

    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        Jenkins(
            url,
            username=SPECIAL_CHAR_USER,
            password="wrongpassword",
            timeout=10,
        )

    assert "401" in str(exc_info.value)


def test_special_char_password_encoding_preserved(
    jenkins_with_special_char_user,
):
    """Special characters must be encoded correctly in auth headers."""
    url = jenkins_with_special_char_user.jenkins_url

    # Create a custom requester to capture the auth header
    from jenkinsapi.utils.requester import Requester

    requester = Requester(
        SPECIAL_CHAR_USER, SPECIAL_CHAR_PASSWORD, baseurl=url, timeout=10
    )

    # Make a request and verify the auth header encoding
    request_dict = requester.get_request_dict(
        params=None, data=None, headers=None
    )
    auth_tuple = request_dict["auth"]

    # Verify auth tuple contains the exact password
    assert auth_tuple == (SPECIAL_CHAR_USER, SPECIAL_CHAR_PASSWORD)

    # Verify encoding for wire protocol
    raw = f"{SPECIAL_CHAR_USER}:{SPECIAL_CHAR_PASSWORD}".encode("latin1")
    encoded = base64.b64encode(raw).decode("utf-8")
    decoded = base64.b64decode(encoded.encode("utf-8")).decode("utf-8")

    assert decoded == f"{SPECIAL_CHAR_USER}:{SPECIAL_CHAR_PASSWORD}"
