# -*- coding: utf-8 -*-
import pytest
from unittest import mock
import json
from . import configs
from jenkinsapi.job import Job
from jenkinsapi.build import Build
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.custom_exceptions import NoBuildData


@pytest.fixture(scope="function")
def jenkins(monkeypatch):
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return {}

    monkeypatch.setattr(Jenkins, "_poll", fake_poll)
    new_jenkins = Jenkins("http://halob:8080/")

    return new_jenkins


@pytest.fixture(scope="function")
def job(jenkins, monkeypatch):
    def fake_get_data(cls, url, tree=None):  # pylint: disable=unused-argument
        return configs.JOB_DATA

    monkeypatch.setattr(JenkinsBase, "get_data", fake_get_data)

    new_job = Job("http://halob:8080/job/foo/", "foo", jenkins)

    return new_job


@pytest.fixture(scope="function")
def job_tree(jenkins, monkeypatch):
    def fake_get_data(cls, url, tree=None):  # pylint: disable=unused-argument
        if tree is not None and "builds" in tree:
            return {"builds": configs.JOB_DATA["builds"]}
        else:
            return {"lastBuild": configs.JOB_DATA["lastBuild"]}

    monkeypatch.setattr(Job, "get_data", fake_get_data)

    new_job = Job("http://halob:8080/job/foo/", "foo", jenkins)

    return new_job


@pytest.fixture(scope="function")
def job_tree_empty(jenkins, monkeypatch):
    def fake_get_data(cls, url, tree=None):  # pylint: disable=unused-argument
        return {}

    monkeypatch.setattr(Job, "get_data", fake_get_data)

    new_job = Job("http://halob:8080/job/foo/", "foo", jenkins)

    return new_job


def test_repr(job):
    # Can we produce a repr string for this object
    assert repr(job) == "<jenkinsapi.job.Job foo>"


def test_name(job):
    with pytest.raises(AttributeError):
        job.id()
    assert job.name == "foo"


def test_next_build_number(job):
    assert job.get_next_build_number() == 4


def test_lastcompleted_build_number(job):
    assert job.get_last_completed_buildnumber() == 3


def test_lastgood_build_number(job):
    assert job.get_last_good_buildnumber() == 3


def test_special_urls(job):
    assert job.baseurl == "http://halob:8080/job/foo"
    assert job.get_delete_url() == "http://halob:8080/job/foo/doDelete"
    assert job.get_rename_url() == "http://halob:8080/job/foo/doRename"


def test_get_description(job):
    assert job.get_description() == "test job"


def test_get_build_triggerurl(job):
    assert (
        job.get_build_triggerurl()
        == "http://halob:8080/job/foo/buildWithParameters"
    )


def test_wrong__mk_json_from_build_parameters(job):
    with pytest.raises(ValueError) as ar:
        job._mk_json_from_build_parameters(build_params="bad parameter")

    assert str(ar.value) == "Build parameters must be a dict"


def test_unicode_mk_json(job):
    json = job._mk_json_from_build_parameters(
        {"age": 20, "name": "品品", "country": "USA", "height": 1.88}
    )
    assert isinstance(json, dict)


def test_wrong_field__build_id_for_type(job):
    with pytest.raises(AssertionError):
        job._buildid_for_type("wrong")


def test_get_last_good_buildnumber(job):
    ret = job.get_last_good_buildnumber()
    assert ret == 3


def test_get_last_stable_buildnumber(job):
    ret = job.get_last_stable_buildnumber()
    assert ret == 3


def test_get_last_failed_buildnumber(job):
    with pytest.raises(NoBuildData):
        job.get_last_failed_buildnumber()


def test_get_last_buildnumber(job):
    ret = job.get_last_buildnumber()
    assert ret == 4


def test_get_last_completed_buildnumber(job):
    ret = job.get_last_completed_buildnumber()
    assert ret == 3


def test_get_build_dict(job_tree):
    ret = job_tree.get_build_dict()
    assert isinstance(ret, dict)
    assert len(ret) == 4


def test_get_build_metadata(job_tree):
    with pytest.raises(ValueError) as ve:
        job_tree.get_build_metadata("abc")

    assert 'Parameter "buildNumber" must be int' in str(ve.value)


def test_nobuilds_get_build_dict(job_tree_empty):
    with pytest.raises(NoBuildData):
        job_tree_empty.get_build_dict()


def test_get_build_ids(job):
    # We don't want to deal with listreverseiterator here
    # So we convert result to a list
    ret = list(job.get_build_ids())
    assert isinstance(ret, list)
    assert len(ret) == 4


def test_nobuilds_get_revision_dict(jenkins, monkeypatch):
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return {"name": "foo"}

    monkeypatch.setattr(Job, "_poll", fake_poll)
    job = Job("http://halob:8080/job/foo/", "foo", jenkins)
    with pytest.raises(NoBuildData):
        job.get_revision_dict()


def test_nobuilds_get_last_build(jenkins, monkeypatch):
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return {"name": "foo"}

    monkeypatch.setattr(Job, "_poll", fake_poll)

    job = Job("http://halob:8080/job/foo/", "foo", jenkins)
    with pytest.raises(NoBuildData):
        job.get_last_build()


def test__add_missing_builds_not_all_loaded(jenkins, monkeypatch):
    def fake_get_data(cls, url, tree):  # pylint: disable=unused-argument
        return configs.JOB_DATA.copy()

    monkeypatch.setattr(JenkinsBase, "get_data", fake_get_data)
    job = Job("http://halob:8080/job/foo/", "foo", jenkins)

    # to test this function we change data to not have one build
    # and set it to mark that firstBuild was not loaded
    # in that condition function will call j.get_data
    # and will use syntetic field 'allBuilds' to
    # repopulate 'builds' field with all builds
    mock_data = configs.JOB_DATA.copy()
    mock_data["firstBuild"] = {"number": 1}
    del mock_data["builds"][-1]
    job._data = mock_data

    assert len(mock_data["builds"]) == 2
    new_data = job._add_missing_builds(mock_data)
    assert len(new_data["builds"]) == 3


def test__add_missing_builds_no_first_build(job, mocker):
    mocker.spy(JenkinsBase, "get_data")

    initial_call_count = job.get_data.call_count
    mock_data = configs.JOB_DATA.copy()
    mock_data["firstBuild"] = None
    job._data = mock_data

    job._add_missing_builds(mock_data)

    assert initial_call_count == job.get_data.call_count


@mock.patch.object(JenkinsBase, "get_data")
def test__add_missing_builds_no_builds(job, mocker):
    mocker.spy(JenkinsBase, "get_data")

    initial_call_count = job.get_data.call_count
    mock_data = configs.JOB_DATA.copy()
    mock_data["builds"] = None
    job._data = mock_data

    job._add_missing_builds(mock_data)

    assert initial_call_count == job.get_data.call_count


def test_get_params(job):
    params = list(job.get_params())
    assert len(params) == 2


def test_get_params_list(job):
    assert job.has_params() is True
    params = job.get_params_list()

    assert isinstance(params, list)
    assert len(params) == 2
    assert params == ["param1", "param2"]


def json_equal(json_a, json_b):
    dict_a = json.loads(json_a)
    dict_b = json.loads(json_b)
    assert dict_a == dict_b


def test_get_json_for_single_param():
    params = {"B": "one two three"}
    expected = (
        '{"parameter": {"name": "B", "value": "one two three"}, '
        '"statusCode": "303", "redirectTo": "."}'
    )
    json_equal(Job.mk_json_from_build_parameters(params), expected)


def test_get_json_for_many_params():
    params = {"B": "Honey", "A": "Boo", "C": 2}
    expected = (
        '{"parameter": [{"name": "A", "value": "Boo"}, '
        '{"name": "B", "value": "Honey"}, '
        '{"name": "C", "value": 2}], '
        '"statusCode": "303", "redirectTo": "."}'
    )

    json_equal(Job.mk_json_from_build_parameters(params), expected)


def test__mk_json_from_build_parameters(job):
    params = {"param1": "value1", "param2": "value2"}
    expected = {
        "parameter": [
            {"name": "param1", "value": "value1"},
            {"name": "param2", "value": "value2"},
        ]
    }
    result = job._mk_json_from_build_parameters(build_params=params)
    assert isinstance(result, dict)

    assert result == expected


def test_wrong_mk_json_from_build_parameters(job):
    with pytest.raises(ValueError) as ar:
        job.mk_json_from_build_parameters(build_params="bad parameter")

    assert "Build parameters must be a dict" in str(ar.value)


def test_get_build_by_params(jenkins, monkeypatch, mocker):
    build_params = {"param1": "value1"}
    fake_builds = (
        mocker.Mock(get_params=lambda: {}),
        mocker.Mock(get_params=lambda: {}),
        mocker.Mock(get_params=lambda: build_params),
    )

    build_call_count = [0]

    def fake_get_build(cls, number):  # pylint: disable=unused-argument
        build_call_count[0] += 1
        return fake_builds[number - 1]

    monkeypatch.setattr(Job, "get_first_buildnumber", lambda x: 1)
    monkeypatch.setattr(Job, "get_last_buildnumber", lambda x: 3)
    monkeypatch.setattr(Job, "get_build", fake_get_build)
    mocker.spy(Build, "get_params")
    mocker.spy(Job, "get_build")

    job = Job("http://localhost/jobs/foo", "foo", jenkins)

    result = job.get_build_by_params(build_params)

    assert job.get_build.call_count == 3
    assert build_call_count[0] == 3
    assert result == fake_builds[2]


def test_get_build_by_params_not_found(jenkins, monkeypatch, mocker):
    build_params = {"param1": "value1"}
    fake_builds = (
        mocker.Mock(get_params=lambda: {}),
        mocker.Mock(get_params=lambda: {}),
        mocker.Mock(get_params=lambda: {}),
    )

    build_call_count = [0]

    def fake_get_build(cls, number):  # pylint: disable=unused-argument
        build_call_count[0] += 1
        return fake_builds[number - 1]

    monkeypatch.setattr(Job, "get_first_buildnumber", lambda x: 1)
    monkeypatch.setattr(Job, "get_last_buildnumber", lambda x: 3)
    monkeypatch.setattr(Job, "get_build", fake_get_build)
    mocker.spy(Build, "get_params")
    mocker.spy(Job, "get_build")

    job = Job("http://localhost/jobs/foo", "foo", jenkins)

    with pytest.raises(NoBuildData):
        job.get_build_by_params(build_params)

    assert job.get_build.call_count == 3
    assert build_call_count[0] == 3
