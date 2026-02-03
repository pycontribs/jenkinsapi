import pytest
import requests
from jenkinsapi.jenkins import Requester
from jenkinsapi.custom_exceptions import JenkinsAPIException
from unittest.mock import patch


def test_no_parameters_uses_default_values():
    req = Requester()
    assert isinstance(req, Requester)
    assert req.username is None
    assert req.password is None
    assert req.ssl_verify
    assert req.cert is None
    assert req.base_scheme is None
    assert req.timeout == 10


def test_all_named_parameters():
    req = Requester(
        username="foo",
        password="bar",
        ssl_verify=False,
        cert="foobar",
        baseurl="http://dummy",
        timeout=5,
    )
    assert isinstance(req, Requester)
    assert req.username == "foo"
    assert req.password == "bar"
    assert not req.ssl_verify
    assert req.cert == "foobar"
    assert req.base_scheme == "http", "dummy"
    assert req.timeout == 5


def test_mix_one_unnamed_named_parameters():
    req = Requester(
        "foo",
        password="bar",
        ssl_verify=False,
        cert="foobar",
        baseurl="http://dummy",
        timeout=5,
    )
    assert isinstance(req, Requester)
    assert req.username == "foo"
    assert req.password == "bar"
    assert not req.ssl_verify
    assert req.cert == "foobar"
    assert req.base_scheme == "http", "dummy"
    assert req.timeout == 5


def test_mix_two_unnamed_named_parameters():
    req = Requester(
        "foo",
        "bar",
        ssl_verify=False,
        cert="foobar",
        baseurl="http://dummy",
        timeout=5,
    )
    assert isinstance(req, Requester)
    assert req.username == "foo"
    assert req.password == "bar"
    assert not req.ssl_verify
    assert req.cert == "foobar"
    assert req.base_scheme == "http", "dummy"
    assert req.timeout == 5


def test_mix_three_unnamed_named_parameters():
    req = Requester(
        "foo", "bar", False, cert="foobar", baseurl="http://dummy", timeout=5
    )
    assert isinstance(req, Requester)
    assert req.username == "foo"
    assert req.password == "bar"
    assert not req.ssl_verify
    assert req.cert == "foobar"
    assert req.base_scheme == "http", "dummy"
    assert req.timeout == 5


def test_mix_four_unnamed_named_parameters():
    req = Requester(
        "foo", "bar", False, "foobar", baseurl="http://dummy", timeout=5
    )
    assert isinstance(req, Requester)
    assert req.username == "foo"
    assert req.password == "bar"
    assert not req.ssl_verify
    assert req.cert == "foobar"
    assert req.base_scheme == "http", "dummy"
    assert req.timeout == 5


def test_mix_five_unnamed_named_parameters():
    req = Requester("foo", "bar", False, "foobar", "http://dummy", timeout=5)
    assert isinstance(req, Requester)
    assert req.username == "foo"
    assert req.password == "bar"
    assert not req.ssl_verify
    assert req.cert == "foobar"
    assert req.base_scheme == "http", "dummy"
    assert req.timeout == 5


def test_all_unnamed_parameters():
    req = Requester("foo", "bar", False, "foobar", "http://dummy", 5)
    assert isinstance(req, Requester)
    assert req.username == "foo"
    assert req.password == "bar"
    assert not req.ssl_verify
    assert req.cert == "foobar"
    assert req.base_scheme == "http", "dummy"
    assert req.timeout == 5


def test_to_much_unnamed_parameters_raises_error():
    with pytest.raises(Exception):
        Requester("foo", "bar", False, "foobar", "http://dummy", 5, "test")


def test_username_without_password_raises_error():
    with pytest.raises(Exception):
        Requester(username="foo")
        Requester("foo")


def test_password_without_username_raises_error():
    with pytest.raises(AssertionError):
        Requester(password="bar")


def test_get_request_dict_auth():
    req = Requester("foo", "bar")

    req_return = req.get_request_dict(params={}, data=None, headers=None)
    assert isinstance(req_return, dict)
    assert req_return.get("auth")
    assert req_return["auth"] == ("foo", "bar")


@patch("jenkinsapi.jenkins.Requester.AUTH_COOKIE", "FAKE")
def test_get_request_dict_cookie():
    req = Requester("foo", "bar")

    req_return = req.get_request_dict(params={}, data=None, headers=None)
    assert isinstance(req_return, dict)
    assert req_return.get("headers")
    assert req_return.get("headers").get("Cookie")
    assert req_return.get("headers").get("Cookie") == "FAKE"


@patch("jenkinsapi.jenkins.Requester.AUTH_COOKIE", "FAKE")
def test_get_request_dict_updatecookie():
    req = Requester("foo", "bar")

    req_return = req.get_request_dict(
        params={}, data=None, headers={"key": "value"}
    )
    assert isinstance(req_return, dict)
    assert req_return.get("headers")
    assert req_return.get("headers").get("key")
    assert req_return.get("headers").get("key") == "value"
    assert req_return.get("headers").get("Cookie")
    assert req_return.get("headers").get("Cookie") == "FAKE"


def test_get_request_dict_nocookie():
    req = Requester("foo", "bar")

    req_return = req.get_request_dict(params={}, data=None, headers=None)
    assert isinstance(req_return, dict)
    assert not req_return.get("headers")


def test_get_request_dict_wrong_params():
    req = Requester("foo", "bar")

    with pytest.raises(AssertionError) as na:
        req.get_request_dict(params="wrong", data=None, headers=None)
    assert "Params must be a dict, got 'wrong'" in str(na.value)


def test_get_request_dict_correct_params():
    req = Requester("foo", "bar")

    req_return = req.get_request_dict(
        params={"param": "value"}, data=None, headers=None
    )

    assert isinstance(req_return, dict)
    assert req_return.get("params")
    assert req_return["params"] == {"param": "value"}


def test_get_request_dict_wrong_headers():
    req = Requester("foo", "bar")

    with pytest.raises(AssertionError) as na:
        req.get_request_dict(params={}, data=None, headers="wrong")
    assert "headers must be a dict, got 'wrong'" in str(na.value)


def test_get_request_dict_correct_headers():
    req = Requester("foo", "bar")

    req_return = req.get_request_dict(
        params={"param": "value"}, data=None, headers={"header": "value"}
    )

    assert isinstance(req_return, dict)
    assert req_return.get("headers")
    assert req_return["headers"] == {"header": "value"}


def test_get_request_dict_data_passed():
    req = Requester("foo", "bar")

    req_return = req.get_request_dict(
        params={"param": "value"},
        data="some data",
        headers={"header": "value"},
    )

    assert isinstance(req_return, dict)
    assert req_return.get("data")
    assert req_return["data"] == "some data"


def test_get_request_dict_data_not_passed():
    req = Requester("foo", "bar")

    req_return = req.get_request_dict(
        params={"param": "value"}, data=None, headers={"header": "value"}
    )

    assert isinstance(req_return, dict)
    assert req_return.get("data") is None


def test_get_url_get(monkeypatch):
    def fake_get(*args, **kwargs):  # pylint: disable=unused-argument
        return "SUCCESS"

    monkeypatch.setattr(requests.Session, "get", fake_get)

    req = Requester("foo", "bar")
    response = req.get_url(
        "http://dummy", params={"param": "value"}, headers=None
    )

    assert response == "SUCCESS"


def test_get_url_post(monkeypatch):
    def fake_post(*args, **kwargs):  # pylint: disable=unused-argument
        return "SUCCESS"

    monkeypatch.setattr(requests.Session, "post", fake_post)

    req = Requester("foo", "bar")
    response = req.post_url(
        "http://dummy", params={"param": "value"}, headers=None
    )

    assert response == "SUCCESS"


def test_post_xml_empty_xml(monkeypatch):
    def fake_post(*args, **kwargs):  # pylint: disable=unused-argument
        return "SUCCESS"

    monkeypatch.setattr(requests.Session, "post", fake_post)

    req = Requester("foo", "bar")
    with pytest.raises(AssertionError):
        req.post_xml_and_confirm_status(
            url="http://dummy", params={"param": "value"}, data=None
        )


def test_post_xml_and_confirm_status_some_xml(monkeypatch):
    class FakeResponse(requests.Response):
        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            self.status_code = 200

    def fake_post(*args, **kwargs):  # pylint: disable=unused-argument
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "post", fake_post)

    req = Requester("foo", "bar")
    ret = req.post_xml_and_confirm_status(
        url="http://dummy", params={"param": "value"}, data="<xml/>"
    )
    assert isinstance(ret, requests.Response)


def test_post_and_confirm_status_empty_data(monkeypatch):
    def fake_post(*args, **kwargs):  # pylint: disable=unused-argument
        return "SUCCESS"

    monkeypatch.setattr(requests.Session, "post", fake_post)

    req = Requester("foo", "bar")
    with pytest.raises(AssertionError):
        req.post_and_confirm_status(
            url="http://dummy", params={"param": "value"}, data=None
        )


def test_post_and_confirm_status_some_data(monkeypatch):
    class FakeResponse(requests.Response):
        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            self.status_code = 200

    def fake_post(*args, **kwargs):  # pylint: disable=unused-argument
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "post", fake_post)

    req = Requester("foo", "bar")
    ret = req.post_and_confirm_status(
        url="http://dummy", params={"param": "value"}, data="some data"
    )
    assert isinstance(ret, requests.Response)


def test_post_and_confirm_status_bad_result(monkeypatch):
    class FakeResponse:
        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            self.status_code = 500
            self.url = "http://dummy"
            self.text = "something"

    def fake_post(*args, **kwargs):  # pylint: disable=unused-argument
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "post", fake_post)

    req = Requester("foo", "bar")
    with pytest.raises(JenkinsAPIException) as error:
        req.post_and_confirm_status(
            url="http://dummy", params={"param": "value"}, data="some data"
        )
    assert "status=500" in str(error)


def test_get_and_confirm_status(monkeypatch):
    class FakeResponse(requests.Response):
        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            self.status_code = 200

    def fake_get(*args, **kwargs):  # pylint: disable=unused-argument
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "get", fake_get)

    req = Requester("foo", "bar")
    ret = req.get_and_confirm_status(
        url="http://dummy", params={"param": "value"}
    )
    assert isinstance(ret, requests.Response)


def test_get_and_confirm_status_bad_result(monkeypatch):
    class FakeResponse:
        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            self.status_code = 500
            self.url = "http://dummy"
            self.text = "something"

    def fake_get(*args, **kwargs):  # pylint: disable=unused-argument
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "get", fake_get)

    req = Requester("foo", "bar", baseurl="http://dummy")
    with pytest.raises(JenkinsAPIException) as error:
        req.get_and_confirm_status(
            url="http://dummy", params={"param": "value"}
        )
    assert "status=500" in str(error)


def test_configure_max_retries():
    req = Requester(
        "username", "password", baseurl="http://dummy", max_retries=3
    )
    for adapter in req.session.adapters.values():
        assert adapter.max_retries.total == 3
