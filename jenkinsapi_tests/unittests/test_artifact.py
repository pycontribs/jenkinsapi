import pytest
from mock import Mock, patch, call
from requests.exceptions import HTTPError
from jenkinsapi.artifact import Artifact
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.fingerprint import Fingerprint
from jenkinsapi.custom_exceptions import ArtifactBroken

try:
    import unittest2 as unittest
except ImportError:
    import unittest


@pytest.fixture()
def artifact(mocker):
    return Artifact(
        "artifact.zip",
        "http://foo/job/TestJob/1/artifact/artifact.zip",
        mocker.MagicMock(),
    )


def test_verify_download_valid_positive(artifact, monkeypatch):
    def fake_md5(cls, fspath):  # pylint: disable=unused-argument
        return "097c42989a9e5d9dcced7b35ec4b0486"

    monkeypatch.setattr(Artifact, "_md5sum", fake_md5)

    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return {}

    monkeypatch.setattr(JenkinsBase, "_poll", fake_poll)

    def fake_validate(
        cls, filename, job, build
    ):  # pylint: disable=unused-argument  # pylint: disable=unused-argument
        return True

    monkeypatch.setattr(Fingerprint, "validate_for_build", fake_validate)

    assert artifact._verify_download(
        "/tmp/artifact.zip", strict_validation=False
    )


def test_verify_download_valid_positive_with_rename(artifact, monkeypatch):
    def fake_md5(cls, fspath):  # pylint: disable=unused-argument
        return "097c42989a9e5d9dcced7b35ec4b0486"

    monkeypatch.setattr(Artifact, "_md5sum", fake_md5)

    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return {}

    monkeypatch.setattr(JenkinsBase, "_poll", fake_poll)

    def fake_validate(
        cls, filename, job, build
    ):  # pylint: disable=unused-argument  # pylint: disable=unused-argument
        return filename == "artifact.zip"

    monkeypatch.setattr(Fingerprint, "validate_for_build", fake_validate)

    assert artifact._verify_download(
        "/tmp/temporary_filename", strict_validation=False
    )


def test_verify_download_valid_negative(artifact, monkeypatch):
    def fake_md5(cls, fspath):  # pylint: disable=unused-argument
        return "097c42989a9e5d9dcced7b35ec4b0486"

    monkeypatch.setattr(Artifact, "_md5sum", fake_md5)

    class FakeResponse(object):
        status_code = 404
        text = "{}"

    class FakeHTTPError(HTTPError):
        def __init__(self):
            self.response = FakeResponse()

    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        raise FakeHTTPError()

    monkeypatch.setattr(JenkinsBase, "_poll", fake_poll)

    def fake_validate(
        cls, filename, job, build
    ):  # pylint: disable=unused-argument  # pylint: disable=unused-argument
        return True

    monkeypatch.setattr(Fingerprint, "validate_for_build", fake_validate)

    assert artifact._verify_download(
        "/tmp/artifact.zip", strict_validation=False
    )


def test_verify_dl_valid_negative_strict(artifact, monkeypatch):
    def fake_md5(cls, fspath):  # pylint: disable=unused-argument
        return "097c42989a9e5d9dcced7b35ec4b0486"

    monkeypatch.setattr(Artifact, "_md5sum", fake_md5)

    class FakeResponse(object):
        status_code = 404
        text = "{}"

    class FakeHTTPError(HTTPError):
        def __init__(self):
            self.response = FakeResponse()

    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        raise FakeHTTPError()

    monkeypatch.setattr(JenkinsBase, "_poll", fake_poll)

    with pytest.raises(ArtifactBroken) as ab:
        artifact._verify_download("/tmp/artifact.zip", strict_validation=True)

    assert (
        "Artifact 097c42989a9e5d9dcced7b35ec4b0486 seems to be broken"
        in str(ab.value)
    )


def test_verify_download_invalid(artifact, monkeypatch):
    def fake_md5(cls, fspath):  # pylint: disable=unused-argument
        return "097c42989a9e5d9dcced7b35ec4b0486"

    monkeypatch.setattr(Artifact, "_md5sum", fake_md5)

    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return {}

    monkeypatch.setattr(JenkinsBase, "_poll", fake_poll)

    def fake_validate(
        cls, filename, job, build
    ):  # pylint: disable=unused-argument  # pylint: disable=unused-argument
        return False

    monkeypatch.setattr(Fingerprint, "validate_for_build", fake_validate)

    with pytest.raises(ArtifactBroken) as ab:
        artifact._verify_download("/tmp/artifact.zip", strict_validation=True)

    assert (
        "Artifact 097c42989a9e5d9dcced7b35ec4b0486 seems to be broken"
        in str(ab.value)
    )


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self._build = build = Mock()
        build.buildno = 9999
        job = self._build.job
        job.jenkins.baseurl = "http://localhost"
        job.name = "TestJob"
        self._artifact = Artifact(
            "artifact.zip",
            "http://localhost/job/TestJob/9999/artifact/artifact.zip",
            build,
        )

    @patch("jenkinsapi.artifact.os.path.exists", spec=True, return_value=True)
    def test_save_has_valid_local_copy(self, mock_exists):
        artifact = self._artifact
        artifact._verify_download = Mock(return_value=True)

        assert artifact.save("/tmp/artifact.zip") == "/tmp/artifact.zip"

        mock_exists.assert_called_once_with("/tmp/artifact.zip")
        artifact._verify_download.assert_called_once_with(
            "/tmp/artifact.zip", False
        )

    @patch("jenkinsapi.artifact.os.path.exists", spec=True, return_value=True)
    def test_save_has_invalid_local_copy_dl_again(self, mock_exists):
        artifact = self._artifact
        artifact._verify_download = Mock(side_effect=[ArtifactBroken, True])
        artifact._do_download = Mock(return_value="/tmp/artifact.zip")

        assert artifact.save("/tmp/artifact.zip", True) == "/tmp/artifact.zip"

        mock_exists.assert_called_once_with("/tmp/artifact.zip")
        artifact._do_download.assert_called_once_with("/tmp/artifact.zip")
        assert (
            artifact._verify_download.mock_calls
            == [call("/tmp/artifact.zip", True)] * 2
        )

    @patch("jenkinsapi.artifact.os.path.exists", spec=True, return_value=True)
    def test_has_invalid_lcl_copy_dl_but_invalid(self, mock_exists):
        artifact = self._artifact
        artifact._verify_download = Mock(
            side_effect=[ArtifactBroken, ArtifactBroken]
        )
        artifact._do_download = Mock(return_value="/tmp/artifact.zip")

        with pytest.raises(ArtifactBroken):
            artifact.save("/tmp/artifact.zip", True)

        mock_exists.assert_called_once_with("/tmp/artifact.zip")
        artifact._do_download.assert_called_once_with("/tmp/artifact.zip")
        assert (
            artifact._verify_download.mock_calls
            == [call("/tmp/artifact.zip", True)] * 2
        )

    @patch("jenkinsapi.artifact.os.path.exists", spec=True, return_value=False)
    def test_save_has_no_local_copy(self, mock_exists):
        artifact = self._artifact
        artifact._do_download = Mock(return_value="/tmp/artifact.zip")
        artifact._verify_download = Mock(return_value=True)

        assert artifact.save("/tmp/artifact.zip") == "/tmp/artifact.zip"

        mock_exists.assert_called_once_with("/tmp/artifact.zip")
        artifact._do_download.assert_called_once_with("/tmp/artifact.zip")
        artifact._verify_download.assert_called_once_with(
            "/tmp/artifact.zip", False
        )
