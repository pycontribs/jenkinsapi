"""
System tests for `jenkinsapi.jenkins` module.
"""

import pytest
from jenkinsapi.job import Job
from jenkinsapi.jobs import Jobs
from jenkinsapi.build import Build
from jenkinsapi.queue import QueueItem
from jenkinsapi_tests.systests.job_configs import EMPTY_JOB
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi.custom_exceptions import UnknownJob


def job_present(jenkins, name):
    jenkins.poll()
    assert name in jenkins, "Job %r is absent in jenkins." % name
    assert isinstance(jenkins.get_job(name), Job) is True
    assert isinstance(jenkins[name], Job) is True


def job_absent(jenkins, name):
    jenkins.poll()
    assert name not in jenkins, "Job %r is present in jenkins." % name


def test_create_job(jenkins):
    job_name = "create_%s" % random_string()
    jenkins.create_job(job_name, EMPTY_JOB)
    job_present(jenkins, job_name)


def test_create_job_with_plus(jenkins):
    job_name = "create+%s" % random_string()
    jenkins.create_job(job_name, EMPTY_JOB)
    job_present(jenkins, job_name)
    job = jenkins[job_name]
    assert job_name in job.url


def test_create_dup_job(jenkins):
    job_name = "create_%s" % random_string()
    old_job = jenkins.create_job(job_name, EMPTY_JOB)
    job_present(jenkins, job_name)
    new_job = jenkins.create_job(job_name, EMPTY_JOB)
    assert new_job == old_job


def test_get_jobs_info(jenkins):
    job_name = "create_%s" % random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    jobs_info = list(jenkins.get_jobs_info())
    assert len(jobs_info) == 1
    for url, name in jobs_info:
        assert url == job.url
        assert name == job.name


def test_create_job_through_jobs_dict(jenkins):
    job_name = "create_%s" % random_string()
    jenkins.jobs[job_name] = EMPTY_JOB
    job_present(jenkins, job_name)


def test_enable_disable_job(jenkins):
    job_name = "create_%s" % random_string()
    jenkins.create_job(job_name, EMPTY_JOB)
    job_present(jenkins, job_name)

    j = jenkins[job_name]
    j.invoke(block=True)  # run this at least once

    j.disable()
    assert j.is_enabled() is False, "A disabled job is reporting incorrectly"

    j.enable()
    assert j.is_enabled() is True, "An enabled job is reporting incorrectly"


def test_get_job_and_update_config(jenkins):
    job_name = "config_%s" % random_string()
    jenkins.create_job(job_name, EMPTY_JOB)
    job_present(jenkins, job_name)
    config = jenkins[job_name].get_config()
    assert config.strip() == EMPTY_JOB.strip()
    jenkins[job_name].update_config(EMPTY_JOB)


def test_invoke_job(jenkins):
    job_name = "create_%s" % random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)
    job.invoke(block=True)
    assert isinstance(job.get_build(1), Build)


def test_invocation_object(jenkins):
    job_name = "create_%s" % random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)
    ii = job.invoke()
    assert isinstance(ii, QueueItem) is True


def test_get_jobs_list(jenkins):
    job1_name = "first_%s" % random_string()
    job2_name = "second_%s" % random_string()

    jenkins.create_job(job1_name, EMPTY_JOB)
    jenkins.create_job(job2_name, EMPTY_JOB)
    assert len(jenkins.jobs) >= 2
    job_list = jenkins.get_jobs_list()
    assert [job1_name, job2_name] == job_list


def test_get_job(jenkins):
    job1_name = "first_%s" % random_string()

    jenkins.create_job(job1_name, EMPTY_JOB)
    job = jenkins[job1_name]
    assert isinstance(job, Job) is True
    assert job.name == job1_name


def test_get_jobs(jenkins):
    job1_name = "first_%s" % random_string()
    job2_name = "second_%s" % random_string()

    jenkins.create_job(job1_name, EMPTY_JOB)
    jenkins.create_job(job2_name, EMPTY_JOB)
    jobs = jenkins.jobs
    assert isinstance(jobs, Jobs) is True
    assert len(jobs) >= 2
    for job_name, job in jobs.iteritems():
        assert isinstance(job_name, str) is True
        assert isinstance(job, Job) is True


def test_get_job_that_does_not_exist(jenkins):
    with pytest.raises(UnknownJob):
        jenkins["doesnot_exist"]


def test_has_job(jenkins):
    job1_name = "first_%s" % random_string()
    jenkins.create_job(job1_name, EMPTY_JOB)
    assert jenkins.has_job(job1_name) is True
    assert job1_name in jenkins


def test_has_no_job(jenkins):
    assert jenkins.has_job("doesnt_exist") is False
    assert "doesnt_exist" not in jenkins


def test_delete_job(jenkins):
    job1_name = "delete_me_%s" % random_string()

    jenkins.create_job(job1_name, EMPTY_JOB)
    jenkins.delete_job(job1_name)
    job_absent(jenkins, job1_name)


def test_rename_job(jenkins):
    job1_name = "A__%s" % random_string()
    job2_name = "B__%s" % random_string()

    jenkins.create_job(job1_name, EMPTY_JOB)
    jenkins.rename_job(job1_name, job2_name)
    job_absent(jenkins, job1_name)
    job_present(jenkins, job2_name)


def test_copy_job(jenkins):
    template_job_name = "TPL%s" % random_string()
    copied_job_name = "CPY%s" % random_string()

    jenkins.create_job(template_job_name, EMPTY_JOB)
    j = jenkins.copy_job(template_job_name, copied_job_name)
    job_present(jenkins, template_job_name)
    job_present(jenkins, copied_job_name)
    assert isinstance(j, Job) is True
    assert j.name == copied_job_name


def test_get_master_data(jenkins):
    master_data = jenkins.get_master_data()
    assert master_data["totalExecutors"] == 2


def test_run_groovy_script(jenkins):
    expected_result = "Hello world!"
    result = jenkins.run_groovy_script('print "%s"' % expected_result)
    assert result.strip() == "Hello world!"
