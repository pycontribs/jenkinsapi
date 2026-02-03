import pytest
from unittest import mock
from jenkinsapi.jenkins import JenkinsBase


@pytest.fixture(scope="function")
def jenkinsbase():
    return JenkinsBase("http://localhost:8080/", poll=False)


def test_called_in__poll(jenkinsbase, monkeypatch, mocker):
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return {
            "description": "My jobs",
            "jobs": [
                {
                    "name": "Foo",
                    "url": "http://localhost:8080/job/Foo",
                    "color": "blue",
                }
            ],
            "name": "All",
            "property": [],
            "url": "http://localhost:8080/view/All/",
        }

    monkeypatch.setattr(JenkinsBase, "_poll", fake_poll)
    stub = mocker.stub()
    monkeypatch.setattr(JenkinsBase, "resolve_job_folders", stub)

    jenkinsbase.poll()

    stub.assert_called_once_with(
        [
            {
                "name": "Foo",
                "url": "http://localhost:8080/job/Foo",
                "color": "blue",
            },
        ],
    )


def test_no_folders(jenkinsbase):
    jobs = [
        {
            "name": "Foo",
            "url": "http://localhost:8080/job/Foo",
            "color": "blue",
        },
        {
            "name": "Bar",
            "url": "http://localhost:8080/job/Bar",
            "color": "disabled",
        },
    ]

    assert jenkinsbase.resolve_job_folders(jobs) == [
        {
            "name": "Foo",
            "url": "http://localhost:8080/job/Foo",
            "color": "blue",
        },
        {
            "name": "Bar",
            "url": "http://localhost:8080/job/Bar",
            "color": "disabled",
        },
    ]


def test_empty_folder(jenkinsbase, monkeypatch, mocker):
    def fake_get_data(cls, url, tree=None):  # pylint: disable=unused-argument
        return {"jobs": []}

    monkeypatch.setattr(JenkinsBase, "get_data", fake_get_data)
    spy = mocker.spy(jenkinsbase, "get_data")

    jobs = [
        {
            "name": "Folder1",
            "url": "http://localhost:8080/job/Folder1",
        },
    ]

    assert jenkinsbase.resolve_job_folders(jobs) == []
    spy.assert_called_once_with(
        "http://localhost:8080/job/Folder1/api/python", tree="jobs[name,color]"
    )


def test_folder_job_mix(jenkinsbase, monkeypatch, mocker):
    def fake_get_data(cls, url, tree=None):  # pylint: disable=unused-argument
        return {
            "jobs": [
                {
                    "name": "Bar",
                    "url": "http://localhost:8080/job/Folder1/job/Bar",
                    "color": "disabled",
                }
            ]
        }

    monkeypatch.setattr(JenkinsBase, "get_data", fake_get_data)
    spy = mocker.spy(jenkinsbase, "get_data")

    jobs = [
        {
            "name": "Foo",
            "url": "http://localhost:8080/job/Foo",
            "color": "blue",
        },
        {
            "name": "Folder1",
            "url": "http://localhost:8080/job/Folder1",
        },
    ]

    assert jenkinsbase.resolve_job_folders(jobs) == [
        {
            "name": "Foo",
            "url": "http://localhost:8080/job/Foo",
            "color": "blue",
        },
        {
            "name": "Bar",
            "url": "http://localhost:8080/job/Folder1/job/Bar",
            "color": "disabled",
        },
    ]

    spy.assert_called_once_with(
        "http://localhost:8080/job/Folder1/api/python", tree="jobs[name,color]"
    )


def test_multiple_folders(jenkinsbase, monkeypatch, mocker):
    def fake_get_data(cls, url, tree=None):  # pylint: disable=unused-argument
        # first call
        if "Folder1" in url:
            return {
                "jobs": [
                    {
                        "name": "Foo",
                        "url": "http://localhost:8080/job/Folder1/job/Foo",
                        "color": "disabled",
                    },
                ]
            }

        if "Folder2" in url:
            # second call
            return {
                "jobs": [
                    {
                        "name": "Bar",
                        "url": "http://localhost:8080/job/Folder2/job/Bar",
                        "color": "blue",
                    },
                ]
            }

    monkeypatch.setattr(JenkinsBase, "get_data", fake_get_data)
    spy = mocker.spy(jenkinsbase, "get_data")

    jobs = [
        {
            "name": "Folder1",
            "url": "http://localhost:8080/job/Folder1",
        },
        {
            "name": "Folder2",
            "url": "http://localhost:8080/job/Folder2",
        },
    ]

    assert jenkinsbase.resolve_job_folders(jobs) == [
        {
            "name": "Foo",
            "url": "http://localhost:8080/job/Folder1/job/Foo",
            "color": "disabled",
        },
        {
            "name": "Bar",
            "url": "http://localhost:8080/job/Folder2/job/Bar",
            "color": "blue",
        },
    ]

    assert spy.call_args_list == [
        mock.call(
            "http://localhost:8080/job/Folder1/api/python",
            tree="jobs[name,color]",
        ),
        mock.call(
            "http://localhost:8080/job/Folder2/api/python",
            tree="jobs[name,color]",
        ),
    ]


def test_multiple_folder_levels(jenkinsbase, monkeypatch, mocker):
    def fake_get_data(cls, url, tree=None):  # pylint: disable=unused-argument
        if "Folder1" in url and "Folder2" not in url:
            # first call
            return {
                "jobs": [
                    {
                        "name": "Bar",
                        "url": "http://localhost:8080/job/Folder1/job/Bar",
                        "color": "disabled",
                    },
                    {
                        "name": "Folder2",
                        "url": "http://localhost:8080/job/Folder1/job/Folder2",
                    },
                ]
            }

        if "Folder2" in url:
            # second call
            return {
                "jobs": [
                    {
                        "name": "Baz",
                        "url": (
                            "http://localhost:8080/job/Folder1/"
                            "job/Folder2/job/Baz"
                        ),
                        "color": "disabled",
                    },
                ]
            }

    monkeypatch.setattr(JenkinsBase, "get_data", fake_get_data)
    spy = mocker.spy(jenkinsbase, "get_data")

    jobs = [
        {
            "name": "Foo",
            "url": "http://localhost:8080/job/Foo",
            "color": "blue",
        },
        {
            "name": "Folder1",
            "url": "http://localhost:8080/job/Folder1",
        },
    ]

    assert jenkinsbase.resolve_job_folders(jobs) == [
        {
            "name": "Foo",
            "url": "http://localhost:8080/job/Foo",
            "color": "blue",
        },
        {
            "name": "Bar",
            "url": "http://localhost:8080/job/Folder1/job/Bar",
            "color": "disabled",
        },
        {
            "name": "Baz",
            "url": ("http://localhost:8080/job/Folder1/job/Folder2/job/Baz"),
            "color": "disabled",
        },
    ]

    assert spy.call_args_list == [
        mock.call(
            "http://localhost:8080/job/Folder1/api/python",
            tree="jobs[name,color]",
        ),
        mock.call(
            "http://localhost:8080/job/Folder1/job/Folder2/api/python",
            tree="jobs[name,color]",
        ),
    ]
