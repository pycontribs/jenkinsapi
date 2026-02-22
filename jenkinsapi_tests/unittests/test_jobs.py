import pytest

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.jobs import Jobs
from jenkinsapi.utils.requester import Requester


@pytest.fixture(scope="function")
def jenkins(mocker, monkeypatch):
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return {}

    monkeypatch.setattr(JenkinsBase, "_poll", fake_poll)
    monkeypatch.setattr(Jenkins, "_poll", fake_poll)

    mock_requester = Requester(username="foouser", password="foopassword")
    mock_requester.post_xml_and_confirm_status = mocker.MagicMock(
        return_value=""
    )

    return Jenkins(
        "http://localhost:8080/",
        username="foouser",
        password="foopassword",
        requester=mock_requester,
    )


def test_create_job_in_folder_path(jenkins):
    jenkins.jobs.create("folder1/folder2/job-name", "<xml/>")

    jenkins.requester.post_xml_and_confirm_status.assert_called_once_with(
        "http://localhost:8080/job/folder1/job/folder2/createItem",
        data="<xml/>",
        params={"name": "job-name"},
    )


def test_create_job_at_root(jenkins):
    jenkins.jobs.create("job-name", "<xml/>")

    jenkins.requester.post_xml_and_confirm_status.assert_called_once_with(
        "http://localhost:8080/createItem",
        data="<xml/>",
        params={"name": "job-name"},
    )


def test_normalizes_job_name_for_contains_and_getitem():
    class DummyJenkins:
        baseurl = "http://localhost:8080/"

    jobs = Jobs(DummyJenkins())
    jobs._data = [
        {
            "name": "folder1/folder2/job-name",
            "url": "http://localhost:8080/job/folder1/job/folder2/job/job-name",
            "color": "blue",
        }
    ]

    assert "folder1/folder2/job-name" in jobs
    assert jobs["folder1/folder2/job-name"].name == (
        "folder1/folder2/job-name"
    )
