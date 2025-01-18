import requests
import pytest
import pytz
from . import configs
import datetime
import warnings
from typing import List
from jenkinsapi.build import Build
from jenkinsapi.job import Job
from jenkinsapi.artifact import Artifact


@pytest.fixture(scope="function")
def jenkins(mocker):
    return mocker.MagicMock()


@pytest.fixture(scope="function")
def job(monkeypatch, jenkins) -> Job:
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return configs.JOB_DATA

    monkeypatch.setattr(Job, "_poll", fake_poll)

    fake_job: Job = Job("http://", "Fake_Job", jenkins)
    return fake_job


@pytest.fixture(scope="function")
def build(job, monkeypatch) -> Build:
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return configs.BUILD_DATA

    monkeypatch.setattr(Build, "_poll", fake_poll)

    return Build("http://", 97, job)


@pytest.fixture(scope="function")
def build_pipeline(job, monkeypatch) -> Build:
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return configs.BUILD_DATA_PIPELINE

    monkeypatch.setattr(Build, "_poll", fake_poll)

    return Build("http://", 97, job)


def test_timestamp(build) -> None:
    assert isinstance(build.get_timestamp(), datetime.datetime)

    expected: datetime.datetime = pytz.utc.localize(
        datetime.datetime(2013, 5, 31, 23, 15, 40)
    )

    assert build.get_timestamp() == expected


def test_name(build) -> None:
    with pytest.raises(AttributeError):
        build.id()
    assert build.name == "foo #1"


def test_duration(build) -> None:
    expected = datetime.timedelta(milliseconds=5782)
    assert build.get_duration() == expected
    assert build.get_duration().seconds == 5
    assert build.get_duration().microseconds == 782000
    assert str(build.get_duration()) == "0:00:05.782000"


def test_get_causes(build) -> None:
    assert build.get_causes() == [
        {
            "shortDescription": "Started by user anonymous",
            "userId": None,
            "userName": "anonymous",
            "upstreamProject": "parentBuild",
            "upstreamBuild": 1,
        }
    ]


def test_get_changeset(build):
    assert build.get_changeset_items() == [
        {
            "affectedPaths": ["content/rcm/v00-rcm-xccdf.xml"],
            "author": {
                "absoluteUrl": "http://jenkins_url/user/username79",
                "fullName": "username",
            },
            "commitId": "3097",
            "timestamp": 1414398423091,
            "date": "2014-10-27T08:27:03.091288Z",
            "msg": "commit message",
            "paths": [
                {"editType": "edit", "file": "/some/path/of/changed_file"}
            ],
            "revision": 3097,
            "user": "username",
        }
    ]


def test_get_changeset_pipeline(build_pipeline):
    assert build_pipeline.get_changeset_items() == [
        {
            "affectedPaths": ["content/rcm/v00-rcm-xccdf.xml"],
            "author": {
                "absoluteUrl": "http://jenkins_url/user/username79",
                "fullName": "username",
            },
            "commitId": "3097",
            "timestamp": 1414398423091,
            "date": "2014-10-27T08:27:03.091288Z",
            "msg": "commit message",
            "paths": [
                {"editType": "edit", "file": "/some/path/of/changed_file"}
            ],
            "revision": 3097,
            "user": "username",
        }
    ]


def test_get_description(build):
    assert build.get_description() == "Best build ever!"


def test_get_slave(build):
    assert build.get_slave() == "localhost"


def test_get_revision_no_scm(build):
    """with no scm, get_revision should return None"""
    assert build.get_revision() is None


def test_downstream(build):
    expected = ["test1", "test2"]
    assert build.get_downstream_job_names() == expected


def test_get_params(build):
    expected = {
        "first_param": "first_value",
        "second_param": "second_value",
    }
    build._data = {
        "actions": [
            {
                "_class": "hudson.model.ParametersAction",
                "parameters": [
                    {"name": "first_param", "value": "first_value"},
                    {"name": "second_param", "value": "second_value"},
                ],
            }
        ]
    }
    params = build.get_params()
    assert params == expected


def test_get_build_url(build):
    expected = "http://foo/1"
    build._data = {"url": "http://foo/1"}
    url = build.get_build_url()
    assert url == expected


def test_get_params_different_order(build):
    """
    Dictionary with `parameters` key is not always the first element in
    `actions` list, so we need to search through whole array. This test
    covers such a case
    """
    expected = {
        "first_param": "first_value",
        "second_param": "second_value",
    }
    build._data = {
        "actions": [
            {
                "not_parameters": "some_data",
            },
            {
                "another_action": "some_value",
            },
            {
                "_class": "hudson.model.ParametersAction",
                "parameters": [
                    {"name": "first_param", "value": "first_value"},
                    {"name": "second_param", "value": "second_value"},
                ],
            },
        ]
    }
    params = build.get_params()
    assert params == expected


def test_only_ParametersAction_parameters_considered(build):
    """Actions other than ParametersAction can have dicts called parameters."""
    expected = {
        "param": "value",
    }
    build._data = {
        "actions": [
            {
                "_class": "hudson.model.SomeOtherAction",
                "parameters": [
                    {"name": "Not", "value": "OurValue"},
                ],
            },
            {
                "_class": "hudson.model.ParametersAction",
                "parameters": [
                    {"name": "param", "value": "value"},
                ],
            },
        ]
    }
    params = build.get_params()
    assert params == expected


def test_ParametersWithNoValueSetValueNone_issue_583(build):
    """SecretParameters don't share their value in the API."""
    expected = {
        "some-secret": None,
    }
    build._data = {
        "actions": [
            {
                "_class": "hudson.model.ParametersAction",
                "parameters": [
                    {"name": "some-secret"},
                ],
            }
        ]
    }
    params = build.get_params()
    assert params == expected


def test_build_env_vars(monkeypatch, build):
    def fake_get_data(cls, tree=None, params=None):
        return configs.BUILD_ENV_VARS

    monkeypatch.setattr(Build, "get_data", fake_get_data)
    assert build.get_env_vars() == configs.BUILD_ENV_VARS["envMap"]


def test_build_env_vars_wo_injected_env_vars_plugin(monkeypatch, build):
    def fake_get_data(cls, tree=None, params=None):
        raise requests.HTTPError("404")

    monkeypatch.setattr(Build, "get_data", fake_get_data)

    with pytest.raises(requests.HTTPError) as excinfo:
        with pytest.warns(UserWarning) as record:
            build.get_env_vars()
    assert "404" == str(excinfo.value)
    assert len(record) == 1
    expected = UserWarning(
        "Make sure the Environment Injector " "plugin is installed."
    )
    assert str(record[0].message) == str(expected)


def test_build_env_vars_other_exception(monkeypatch, build):
    def fake_get_data(cls, tree=None, params=None):
        raise ValueError()

    monkeypatch.setattr(Build, "get_data", fake_get_data)

    with pytest.raises(Exception) as excinfo:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            build.get_env_vars()
    assert "" == str(excinfo.value)


def test_build_get_status(build) -> None:
    assert build.get_status() == "SUCCESS"


def test_build_get_params_return_empty_dict(build) -> None:
    build._data = {"actions": []}
    assert build.get_params() == {}


def test_build_get_changeset_empty(build) -> None:
    build._data = {"changeSet": {}}
    assert build.get_changeset_items() == []


def test_build_get_changesets_vcs(build) -> None:
    # This test shall test lines 162-164 in build.py
    build._data = {"changeSets": {"kind": "git"}}
    assert build._get_vcs() == "git"


def test_build_get_number(build) -> None:
    assert build.get_number() == 1


def test_build_get_artifacts(build) -> None:
    afs: List[Artifact] = list(build.get_artifacts())
    assert len(afs) == 1
    assert isinstance(afs[0], Artifact)
    assert list(afs)[0].filename == "foo.txt"


def test_build_get_upstream_job_name(build) -> None:
    assert build.get_upstream_job_name() == "parentBuild"


def test_build_get_ustream_job_name_none(build) -> None:
    build._data = {"actions": []}
    assert build.get_upstream_job_name() is None


def test_build_get_master_job_name(build) -> None:
    assert build.get_master_job_name() == "masterBuild"


def test_build_get_master_build_number(build) -> None:
    assert build.get_master_build_number() == 1
