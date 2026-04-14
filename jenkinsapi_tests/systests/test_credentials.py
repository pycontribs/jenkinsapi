"""
System tests for `jenkinsapi.jenkins` module.
"""

import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.test_utils.retry import retry
from jenkinsapi.credentials import Credentials
from jenkinsapi.credentials import UsernamePasswordCredential
from jenkinsapi.credentials import SecretTextCredential
from jenkinsapi.credential import SSHKeyCredential
from jenkinsapi.credential import FileCredentials
from jenkinsapi.credential import DockerServerCredentials

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


@retry()
def test_get_credentials(jenkins):
    creds = jenkins.credentials
    assert isinstance(creds, Credentials) is True


def test_delete_inexistant_credential(jenkins):
    with pytest.raises(KeyError):
        creds = jenkins.credentials

        del creds[random_string()]


@retry()
def test_create_user_pass_credential(jenkins):
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


@retry()
def test_update_user_pass_credential(jenkins):
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


@retry()
def test_create_ssh_credential(jenkins):
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


@retry()
def test_delete_credential(jenkins):
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


@retry()
def test_create_secret_text_credential(jenkins):
    """
    Tests the creation of a secret text.
    """
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


@retry()
def test_create_file_credential(jenkins):
    import base64

    creds = jenkins.credentials

    cred_descr = random_string()
    secret_content = b"my secret file content"
    cred_dict = {
        "description": cred_descr,
        "filename": "secret.txt",
        "secret_bytes": base64.b64encode(secret_content).decode("utf-8"),
    }
    creds[cred_descr] = FileCredentials(cred_dict)

    assert cred_descr in creds
    cred = creds[cred_descr]
    assert isinstance(cred, FileCredentials)


@retry()
def test_create_docker_server_credential(jenkins):
    creds = jenkins.credentials

    cred_descr = random_string()
    cred_dict = {
        "description": cred_descr,
        "username": "dockeruser",
        "clientKey": "-----BEGIN RSA PRIVATE KEY-----\nclient-key\n-----END RSA PRIVATE KEY-----",
        "clientCertificate": "-----BEGIN CERTIFICATE-----\nclient-cert\n-----END CERTIFICATE-----",
        "serverCaCertificate": "-----BEGIN CERTIFICATE-----\nca-cert\n-----END CERTIFICATE-----",
    }
    creds[cred_descr] = DockerServerCredentials(cred_dict)

    assert cred_descr in creds
    cred = creds[cred_descr]
    assert isinstance(cred, DockerServerCredentials)
    assert cred.description == cred_descr

    del creds[cred_descr]
    assert cred_descr not in creds
