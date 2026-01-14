from jenkinsapi_tests.systests.job_configs import (
    PIPELINE_SCM_CONF_TEST_PARAMS,
    PIPELINE_SCM_JOB,
)
from jenkinsapi_tests.test_utils.random_strings import random_string


def test_pipeline_scm(jenkins):
    """
    Can we extract scm info from a pipeline scm job?
    """
    job_name = random_string()
    job = jenkins.create_job(job_name, PIPELINE_SCM_JOB)
    assert (
        job.get_scm_type()
        == job._scm_map[PIPELINE_SCM_CONF_TEST_PARAMS["scm_class"]]
    )
    assert job.get_scm_url()[0] == PIPELINE_SCM_CONF_TEST_PARAMS["git_url"]
