"""
System tests for `jenkinsapi.jenkins` module.
"""

import time
import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi.credentials import Credentials
from jenkinsapi.credentials import UsernamePasswordCredential
from jenkinsapi.credentials import SecretTextCredential
from jenkinsapi.credential import SSHKeyCredential

log = logging.getLogger(__name__)


def test_get_credentials(jenkins):
    # Retry with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            creds = jenkins.credentials
            assert isinstance(creds, Credentials) is True
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error


def test_delete_inexistant_credential(jenkins):
    with pytest.raises(KeyError):
        creds = jenkins.credentials

        del creds[random_string()]


def test_create_user_pass_credential(jenkins):
    # Retry with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            creds = jenkins.credentials

            cred_descr = random_string()
            cred_dict = {
                "description": cred_descr,
                "userName": "userName",
                "password": "password",
            }
            creds[cred_descr] = UsernamePasswordCredential(cred_dict)

            assert cred_descr in creds

            cred = creds[cred_descr]
            assert isinstance(cred, UsernamePasswordCredential) is True
            assert cred.password == ""
            assert cred.description == cred_descr

            del creds[cred_descr]
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error


def test_update_user_pass_credential(jenkins):
    # Retry with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            creds = jenkins.credentials

            cred_descr = random_string()
            cred_dict = {
                "description": cred_descr,
                "userName": "userName",
                "password": "password",
            }
            creds[cred_descr] = UsernamePasswordCredential(cred_dict)

            cred = creds[cred_descr]
            cred.userName = "anotheruser"
            cred.password = "password2"

            cred = creds[cred_descr]
            assert isinstance(cred, UsernamePasswordCredential) is True
            assert cred.userName == "anotheruser"
            assert cred.password == "password2"
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error


def test_create_ssh_credential(jenkins):
    # Retry with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            creds = jenkins.credentials

            cred_descr = random_string()
            cred_dict = {
                "description": cred_descr,
                "userName": "userName",
                "passphrase": "",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----",
            }
            creds[cred_descr] = SSHKeyCredential(cred_dict)

            assert cred_descr in creds

            cred = creds[cred_descr]
            assert isinstance(cred, SSHKeyCredential) is True
            assert cred.description == cred_descr

            del creds[cred_descr]

            cred_dict = {
                "description": cred_descr,
                "userName": "userName",
                "passphrase": "",
                "private_key": "/tmp/key",
            }
            with pytest.raises(ValueError):
                creds[cred_descr] = SSHKeyCredential(cred_dict)

            cred_dict = {
                "description": cred_descr,
                "userName": "userName",
                "passphrase": "",
                "private_key": "~/.ssh/key",
            }
            with pytest.raises(ValueError):
                creds[cred_descr] = SSHKeyCredential(cred_dict)

            cred_dict = {
                "description": cred_descr,
                "userName": "userName",
                "passphrase": "",
                "private_key": "invalid",
            }
            with pytest.raises(ValueError):
                creds[cred_descr] = SSHKeyCredential(cred_dict)
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error


def test_delete_credential(jenkins):
    # Retry with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            creds = jenkins.credentials

            cred_descr = random_string()
            cred_dict = {
                "description": cred_descr,
                "userName": "userName",
                "password": "password",
            }
            creds[cred_descr] = UsernamePasswordCredential(cred_dict)

            assert cred_descr in creds
            del creds[cred_descr]
            assert cred_descr not in creds
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error


def test_create_secret_text_credential(jenkins):
    """
    Tests the creation of a secret text.
    """
    # Retry with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            creds = jenkins.credentials

            cred_descr = random_string()
            cred_dict = {"description": cred_descr, "secret": "newsecret"}
            creds[cred_descr] = SecretTextCredential(cred_dict)

            assert cred_descr in creds
            cred = creds[cred_descr]
            assert isinstance(cred, SecretTextCredential) is True
            assert cred.secret is None
            assert cred.description == cred_descr

            del creds[cred_descr]
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error
