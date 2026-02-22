import pytest
import hashlib
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.fingerprint import Fingerprint
from jenkinsapi.utils.requester import Requester
from requests.exceptions import HTTPError


@pytest.fixture(scope="function")
def jenkins(monkeypatch):
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return {}

    monkeypatch.setattr(Jenkins, "_poll", fake_poll)

    return Jenkins(
        "http://localhost:8080", username="foouser", password="foopassword"
    )


@pytest.fixture(scope="module")
def dummy_md5():
    md = hashlib.md5()
    md.update("some dummy string".encode("ascii"))
    return md.hexdigest()


def test_object_creation(jenkins, dummy_md5, monkeypatch):
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return {}

    monkeypatch.setattr(JenkinsBase, "_poll", fake_poll)
    fp_instance = Fingerprint("http://foo:8080", dummy_md5, jenkins)

    assert isinstance(fp_instance, Fingerprint)
    assert str(fp_instance) == dummy_md5
    assert fp_instance.valid()


def test_valid_for_404(jenkins, dummy_md5, monkeypatch):
    class FakeResponse:
        status_code = 404
        text = "{}"

    class FakeHTTPError(HTTPError):
        def __init__(self):
            self.response = FakeResponse()

    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        raise FakeHTTPError()

    monkeypatch.setattr(JenkinsBase, "_poll", fake_poll)

    def fake_get_url(
        url,  # pylint: disable=unused-argument
        params=None,  # pylint: disable=unused-argument
        headers=None,  # pylint: disable=unused-argument
        allow_redirects=True,  # pylint: disable=unused-argument
        stream=False,
    ):  # pylint: disable=unused-argument
        return FakeResponse()

    monkeypatch.setattr(Requester, "get_url", fake_get_url)

    fingerprint = Fingerprint("http://foo:8080", dummy_md5, jenkins)
    assert fingerprint.valid() is True


def test_invalid_for_401(jenkins, dummy_md5, monkeypatch):
    class FakeResponse:
        status_code = 401
        text = "{}"

    class FakeHTTPError(HTTPError):
        def __init__(self):
            self.response = FakeResponse()

    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        raise FakeHTTPError()

    monkeypatch.setattr(JenkinsBase, "_poll", fake_poll)

    def fake_get_url(
        url,  # pylint: disable=unused-argument
        params=None,  # pylint: disable=unused-argument
        headers=None,  # pylint: disable=unused-argument
        allow_redirects=True,  # pylint: disable=unused-argument
        stream=False,
    ):  # pylint: disable=unused-argument
        return FakeResponse()

    monkeypatch.setattr(Requester, "get_url", fake_get_url)

    fingerprint = Fingerprint("http://foo:8080", dummy_md5, jenkins)
    assert fingerprint.valid() is not True
