import pytest
from jenkinsapi_tests.systests.job_configs import (
    PIPELINE_SCM_CONF_TEST_PARAMS,
    PIPELINE_SCM_JOB,
)
from jenkinsapi.build import Build
from jenkinsapi.job import Job


@pytest.fixture(scope="function")
def jenkins(mocker):
    return mocker.MagicMock()


@pytest.fixture(scope="function")
def job(monkeypatch, jenkins):
    def fake_get_config(cls, tree=None):  # pylint: disable=unused-argument
        return PIPELINE_SCM_JOB

    monkeypatch.setattr(Job, "get_config", fake_get_config)

    fake_job = Job("http://", "Fake_Job", jenkins)
    return fake_job


def test_pipeline_scm(job: Job):
    """
    Can we extract git build revision data from a build object?
    """
    assert (
        job.get_scm_type()
        == job._scm_map[PIPELINE_SCM_CONF_TEST_PARAMS["scm_class"]]
    )
    assert job.get_scm_url()[0] == PIPELINE_SCM_CONF_TEST_PARAMS["git_url"]
