# '''
# System tests for `jenkinsapi.jenkins` module.
# '''
from testfixtures import compare
from time import sleep

from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import (
    SCM_GIT_JOB,
    MULTIBRANCH_GIT_BRANCH_JOB_PROPERTY,
)


def wait_for_job_setup(jenkins, job_name):
    for _ in range(5):
        for _url, name in list(jenkins.get_jobs_info()):
            if job_name in name:
                return True
            else:
                sleep(10)


def test_get_scm_type(jenkins):
    job_name = "git_%s" % random_string()
    job = jenkins.create_job(job_name, SCM_GIT_JOB)
    wait_for_job_setup(jenkins, job_name)
    compare(job.get_scm_type(), "git")
    jenkins.delete_job(job_name)


def test_get_scm_type_pipeline_scm_multibranch_BranchJobProperty(
    jenkins,
):
    job_name = "git_%s" % random_string()
    job = jenkins.create_job(job_name, MULTIBRANCH_GIT_BRANCH_JOB_PROPERTY)
    wait_for_job_setup(jenkins, job_name)
    compare(job.get_scm_type(), "git")


### Disabling for now, running into permissions errors
# def test_get_scm_type_pipeline_scm_multibranch_BranchSource(
#    jenkins,
# ):
#    job_name = "git_%s" % random_string()
#    job = jenkins.create_multibranch_pipeline_job(
#        job_name, MULTIBRANCH_GIT_SCM_JOB
#    )
#    wait_for_job_setup(jenkins, job_name)
#    job.invoke(block=True, delay=20)
#    compare(job[0].get_scm_type(), "git")
#
#
# def test_get_scm_type_pipeline_github_multibranch_BranchSource(
#    jenkins,
# ):
#    job_name = "git_%s" % random_string()
#    job = jenkins.create_multibranch_pipeline_job(
#        job_name, MULTIBRANCH_GITHUB_SCM_JOB
#    )
#    wait_for_job_setup(jenkins, job_name)
#    job.invoke(block=True, delay=20)
#    compare(job.get_scm_type(), "github")
