"""
System tests for authentication functionality
"""

import time
import pytest
from jenkinsapi.utils.requester import Requester
from requests import HTTPError as REQHTTPError
from jenkinsapi.jenkins import Jenkins


def test_normal_authentication(jenkins_admin_admin):
    # Retry with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            # No problem with the righ user/pass
            jenkins_user = Jenkins(
                jenkins_admin_admin.baseurl,
                jenkins_admin_admin.username,
                jenkins_admin_admin.password,
            )

            assert jenkins_user is not None

            # We cannot connect if no user/pass
            with pytest.raises(REQHTTPError) as http_excep:
                Jenkins(jenkins_admin_admin.baseurl)

            assert Requester.AUTH_COOKIE is None
            assert http_excep.value.response.status_code == 403
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error


#    def test_auth_cookie(jenkins_admin_admin):
#        initial_cookie_value = None
#        final_cookie_value = "JSESSIONID"
#        assert initial_cookie_value == Requester.AUTH_COOKIE
#
#        jenkins_admin_admin.use_auth_cookie()
#
#        result = Requester.AUTH_COOKIE
#        assert result is not None
#        assert final_cookie_value in result
#
#
#    def test_wrongauth_cookie(jenkins_admin_admin):
#        initial_cookie_value = None
#        assert initial_cookie_value == Requester.AUTH_COOKIE
#
#        jenkins_admin_admin.username = "fakeuser"
#        jenkins_admin_admin.password = "fakepass"
#
#        with pytest.raises(HTTPError) as http_excep:
#            jenkins_admin_admin.use_auth_cookie()
#
#        assert Requester.AUTH_COOKIE is None
#        assert http_excep.value.code == 401
#
#
#    def test_verify_cookie_isworking(jenkins_admin_admin):
#        initial_cookie_value = None
#        final_cookie_value = "JSESSIONID"
#        assert initial_cookie_value == Requester.AUTH_COOKIE
#
#        # Remove requester user/pass
#        jenkins_admin_admin.requester.username = None
#        jenkins_admin_admin.requester.password = None
#
#        # Verify that we cannot connect
#        with pytest.raises(REQHTTPError) as http_excep:
#            jenkins_admin_admin.poll()
#
#        assert Requester.AUTH_COOKIE is None
#        assert http_excep.value.response.status_code == 403
#
#        # Retrieve the auth cookie, we can because we
#        # have right values for jenkins_admin_admin.username
#        # and jenkins_admin_admin.password
#        jenkins_admin_admin.use_auth_cookie()
#
#        result = Requester.AUTH_COOKIE
#        assert result is not None
#        assert final_cookie_value in result
#
#        # Verify that we can connect even with no requester user/pass
#        # If we have the cookie the requester user/pass is not needed
#        jenkins_admin_admin.poll()
