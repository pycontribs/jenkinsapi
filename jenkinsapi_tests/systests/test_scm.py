# '''
# System tests for `jenkinsapi.jenkins` module.
# '''
# To run unittests on python 2.6 please use unittest2 library
# try:
# import unittest2 as unittest
# except ImportError:
# import unittest
import pytest
from testfixtures import compare

from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi.utils.crumb_requester import CrumbRequester
from jenkinsapi_tests.systests.job_configs import (
    SCM_GIT_JOB,
    JOB_WITH_ARTIFACTS,
    PIPELINE_SCM_JOB,
    MULTIBRANCH_GIT_BRANCH_JOB_PROPERTY,
    MULTIBRANCH_GIT_SCM_JOB,
    MULTIBRANCH_GITHUB_SCM_JOB,
)
from jenkinsapi.custom_exceptions import NotConfiguredSCM, NotSupportSCM


def test_get_scm_type(jenkins_admin_admin):
    job_name = "git_%s" % random_string()
    job = jenkins_admin_admin.create_job(job_name, SCM_GIT_JOB)
    compare(job.get_scm_type(), "git")
    jenkins_admin_admin.delete_job(job_name)


def test_get_scm_type_pipeline_scm_multibranch_BranchJobProperty(
    jenkins_admin_admin,
):
    job_name = "git_%s" % random_string()
    jenkins_admin_admin.requester = CrumbRequester(
        baseurl=jenkins_admin_admin.baseurl,
        username=jenkins_admin_admin.username,
        password=jenkins_admin_admin.password,
    )
    job = jenkins_admin_admin.create_job(
        job_name, MULTIBRANCH_GIT_BRANCH_JOB_PROPERTY
    )
    job.invoke(block=True, delay=20)
    compare(job.get_scm_type(), "git")


def test_get_scm_type_pipeline_scm_multibranch_BranchSource(
    jenkins_admin_admin,
):
    job_name = "git_%s" % random_string()
    job = jenkins_admin_admin.create_multibranch_pipeline_job(
        job_name, MULTIBRANCH_GIT_SCM_JOB
    )
    job.invoke(block=True, delay=20)
    compare(job[0].get_scm_type(), "git")


def test_get_scm_type_pipeline_github_multibranch_BranchSource(
    jenkins_admin_admin,
):
    job_name = "git_%s" % random_string()
    job = jenkins_admin_admin.create_multibranch_pipeline_job(
        job_name, MULTIBRANCH_GITHUB_SCM_JOB
    )
    job.invoke(block=True, delay=20)
    compare(job.get_scm_type(), "github")
