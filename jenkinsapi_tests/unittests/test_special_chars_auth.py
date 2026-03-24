"""
Tests to reproduce issue #862: Auth when password has special characters fails.
https://github.com/pycontribs/jenkinsapi/issues/862
"""

import base64
import pytest
import requests

from jenkinsapi.utils.requester import Requester
from jenkinsapi.jenkins import Jenkins


class FakeResponse(requests.Response):
    def __init__(self, status_code=200, content=b"{'jobs': []}"):
        super().__init__()
        self.status_code = status_code
        self._content = content


def test_requester_preserves_special_chars_in_password():
    """Password with special characters must be stored unchanged (issue #862)."""
    password = "zzzzzz6@Y74(K.xxxxxxx"
    req = Requester("testuser", password)
    assert req.password == password


def test_auth_tuple_contains_exact_special_char_password():
    """Auth tuple passed to requests must contain the exact password (issue #862)."""
    password = "zzzzzz6@Y74(K.xxxxxxx"
    req = Requester("testuser", password)
    request_dict = req.get_request_dict(params=None, data=None, headers=None)
    assert request_dict["auth"] == ("testuser", password)


def test_authorization_header_correctly_encodes_special_chars(monkeypatch):
    """Wire Authorization header must correctly base64-encode passwords with
    special characters like @ ( ) . — reproduces issue #862."""
    password = "zzzzzz6@Y74(K.xxxxxxx"
    captured = {}

    def fake_get(self, url, **kwargs):
        u, p = kwargs["auth"]
        raw = f"{u}:{p}".encode("latin1")
        captured["decoded"] = base64.b64decode(base64.b64encode(raw)).decode(
            "utf-8"
        )
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "get", fake_get)

    Requester("testuser", password, baseurl="http://dummy").get_url(
        "http://dummy"
    )

    assert captured["decoded"] == f"testuser:{password}"


def test_jenkins_init_succeeds_with_special_char_password(monkeypatch):
    """Jenkins.__init__ must not raise when password has special characters
    and the server returns 200 — reproduces issue #862."""
    monkeypatch.setattr(
        requests.Session,
        "get",
        lambda self, url, **kw: FakeResponse(
            content=b"{'_class': 'hudson.model.Hudson', 'jobs': []}"
        ),
    )
    j = Jenkins(
        "http://dummy",
        username="testuser",
        password="zzzzzz6@Y74(K.xxxxxxx",
        timeout=10,
        use_crumb=False,
    )
    assert j.password == "zzzzzz6@Y74(K.xxxxxxx"


def test_jenkins_raises_401_with_special_char_password(monkeypatch):
    """A 401 from the server must propagate as HTTPError regardless of special
    chars in the password — exact scenario from issue #862."""
    monkeypatch.setattr(
        requests.Session,
        "get",
        lambda self, url, **kw: FakeResponse(status_code=401),
    )
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        Jenkins(
            "http://dummy",
            username="testuser",
            password="zzzzzz6@Y74(K.xxxxxxx",
            timeout=10,
            use_crumb=False,
        )
    assert "401" in str(exc_info.value)
