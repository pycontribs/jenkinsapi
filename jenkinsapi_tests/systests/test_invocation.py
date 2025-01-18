"""
System tests for `jenkinsapi.jenkins` module.
"""

import time
import logging
import pytest
from jenkinsapi.build import Build
from jenkinsapi.queue import QueueItem
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import LONG_RUNNING_JOB
from jenkinsapi_tests.systests.job_configs import SHORTISH_JOB, EMPTY_JOB
from jenkinsapi.custom_exceptions import BadParams, NotFound


log = logging.getLogger(__name__)


def test_invocation_object(jenkins):
    job_name = "Acreate_%s" % random_string()
    job = jenkins.create_job(job_name, SHORTISH_JOB)
    qq = job.invoke()
    assert isinstance(qq, QueueItem)
    # Let Jenkins catchup
    qq.block_until_building()
    assert qq.get_build_number() == 1


def test_get_block_until_build_running(jenkins):
    job_name = "Bcreate_%s" % random_string()
    job = jenkins.create_job(job_name, LONG_RUNNING_JOB)
    qq = job.invoke()
    time.sleep(3)
    bn = qq.block_until_building(delay=3).get_number()
    assert isinstance(bn, int)

    build = qq.get_build()
    assert isinstance(build, Build)
    assert build.is_running()
    build.stop()
    # if we call next line right away - Jenkins have no time to stop job
    # so we wait a bit
    time.sleep(1)
    assert not build.is_running()
    console = build.get_console()
    assert isinstance(console, str)
    assert "Started by user" in console


def test_get_block_until_build_complete(jenkins):
    job_name = "Ccreate_%s" % random_string()
    job = jenkins.create_job(job_name, SHORTISH_JOB)
    qq = job.invoke()
    qq.block_until_complete()
    assert not qq.get_build().is_running()


def test_mi_and_get_last_build(jenkins):
    job_name = "Dcreate_%s" % random_string()

    job = jenkins.create_job(job_name, SHORTISH_JOB)

    for _ in range(3):
        ii = job.invoke()
        ii.block_until_complete(delay=2)

    build_number = job.get_last_good_buildnumber()
    assert build_number == 3

    build = job.get_build(build_number)
    assert isinstance(build, Build)

    build = job.get_build_metadata(build_number)
    assert isinstance(build, Build)


def test_mi_and_get_build_number(jenkins):
    job_name = "Ecreate_%s" % random_string()

    job = jenkins.create_job(job_name, EMPTY_JOB)

    for invocation in range(3):
        qq = job.invoke()
        qq.block_until_complete(delay=1)
        build_number = qq.get_build_number()
        assert build_number == invocation + 1


def test_mi_and_delete_build(jenkins):
    job_name = "Ecreate_%s" % random_string()

    job = jenkins.create_job(job_name, EMPTY_JOB)

    for invocation in range(3):
        qq = job.invoke()
        qq.block_until_complete(delay=1)
        build_number = qq.get_build_number()
        assert build_number == invocation + 1

    # Delete build using Job.delete_build
    job.get_build(1)
    job.delete_build(1)
    with pytest.raises(NotFound):
        job.get_build(1)

    # Delete build using Job as dictionary of builds
    assert isinstance(job[2], Build)
    del job[2]

    with pytest.raises(NotFound):
        job.get_build(2)

    with pytest.raises(NotFound):
        job.delete_build(99)


def test_give_params_on_non_parameterized_job(jenkins):
    job_name = "Ecreate_%s" % random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)
    with pytest.raises(BadParams):
        job.invoke(build_params={"foo": "bar", "baz": 99})


def test_keep_build_toggle(jenkins):
    job_name = "Ecreate_%s" % random_string()

    job = jenkins.create_job(job_name, EMPTY_JOB)

    qq = job.invoke()
    qq.block_until_complete(delay=1)

    build = job.get_last_build()
    assert not build.is_kept_forever()
    build.toggle_keep()
    assert build.is_kept_forever()

    build_number = job.get_last_buildnumber()
    job.toggle_keep_build(build_number)
    build = job.get_last_build()
    assert not build.is_kept_forever()
