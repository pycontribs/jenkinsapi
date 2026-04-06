import base64

from jenkinsapi.credential import DockerServerCredentials
from jenkinsapi.credential import FileCredentials
from jenkinsapi.credentials import Credentials


def test_make_credential_recognizes_docker_x509_type():
    creds = object.__new__(Credentials)

    credential = creds._make_credential(
        {
            "description": "docker cert",
            "typeName": "X.509 Client Certificate",
        }
    )

    assert isinstance(credential, DockerServerCredentials)


def test_file_credentials_create_files_payload_decodes_secret_bytes():
    secret_bytes = base64.b64encode(b"secret payload").decode("ascii")
    credential = FileCredentials(
        {
            "description": "file cred",
            "filename": "secret.txt",
            "secret_bytes": secret_bytes,
        }
    )

    assert credential.get_files() == {
        "file0": ("secret.txt", b"secret payload")
    }
