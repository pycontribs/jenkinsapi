"""
System tests for `jenkinsapi.jenkins` module.
"""

import io
import time

from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import JOB_WITH_FILE
from jenkinsapi_tests.systests.job_configs import JOB_WITH_FILE_AND_PARAMS
from jenkinsapi_tests.systests.job_configs import JOB_WITH_PARAMETERS


def test_invoke_job_with_file(jenkins):
    file_data = random_string()
    param_file = io.BytesIO(file_data.encode("utf-8"))

    job_name = "create1_%s" % random_string()
    job = jenkins.create_job(job_name, JOB_WITH_FILE)

    assert job.has_params() is True
    assert len(job.get_params_list()) != 0

    job.invoke(block=True, files={"file.txt": param_file})

    build = job.get_last_build()
    while build.is_running():
        time.sleep(0.25)

    artifacts = build.get_artifact_dict()
    assert isinstance(artifacts, dict) is True
    art_file = artifacts["file.txt"]
    assert art_file.get_data().decode("utf-8").strip() == file_data


def test_invoke_job_parameterized(jenkins):
    param_B = random_string()

    job_name = "create2_%s" % random_string()
    job = jenkins.create_job(job_name, JOB_WITH_PARAMETERS)
    job.invoke(block=True, build_params={"B": param_B})
    build = job.get_last_build()

    artifacts = build.get_artifact_dict()
    artB = artifacts["b.txt"]
    assert artB.get_data().decode("UTF-8", "replace").strip() == param_B

    assert param_B in build.get_console()


def test_parameterized_job_build_queuing(jenkins):
    """
    Accept multiple builds of parameterized jobs with unique parameters.
    """
    job_name = "create_%s" % random_string()
    job = jenkins.create_job(job_name, JOB_WITH_PARAMETERS)

    # Latest Jenkins schedules builds to run right away, so remove all
    # executors from master node to investigate queue
    master = jenkins.nodes["Built-In Node"]
    num_executors = master.get_num_executors()
    master.set_num_executors(0)

    for i in range(3):
        param_B = random_string()
        params = {"B": param_B}
        job.invoke(build_params=params)

    assert job.has_queued_build(params) is True

    master.set_num_executors(num_executors)

    while job.has_queued_build(params):
        time.sleep(0.25)

    build = job.get_last_build()
    while build.is_running():
        time.sleep(0.25)

    artifacts = build.get_artifact_dict()
    assert isinstance(artifacts, dict) is True
    artB = artifacts["b.txt"]
    assert artB.get_data().decode("utf-8").strip() == param_B

    assert param_B in build.get_console()


def test_parameterized_multiple_builds_get_the_same_queue_item(jenkins):
    """
    Multiple attempts to run the same parameterized
    build will get the same queue item.
    """
    job_name = "create_%s" % random_string()
    job = jenkins.create_job(job_name, JOB_WITH_PARAMETERS)

    # Latest Jenkins schedules builds to run right away, so remove all
    # executors from master node to investigate queue
    master = jenkins.nodes["Built-In Node"]
    num_executors = master.get_num_executors()
    master.set_num_executors(0)

    for i in range(3):
        params = {"B": random_string()}
        qq0 = job.invoke(build_params=params)

    qq1 = job.invoke(build_params=params)
    assert qq0 == qq1

    master.set_num_executors(num_executors)


def test_invoke_job_with_file_and_params(jenkins):
    file_data = random_string()
    param_data = random_string()
    param_file = io.BytesIO(file_data.encode("utf-8"))

    job_name = "create_%s" % random_string()
    job = jenkins.create_job(job_name, JOB_WITH_FILE_AND_PARAMS)

    assert job.has_params() is True
    assert len(job.get_params_list()) != 0

    qi = job.invoke(
        block=True,
        files={"file.txt": param_file},
        build_params={"B": param_data},
    )

    build = qi.get_build()
    artifacts = build.get_artifact_dict()
    assert isinstance(artifacts, dict) is True
    art_file = artifacts["file.txt"]
    assert art_file.get_data().decode("utf-8").strip() == file_data
    art_param = artifacts["file1.txt"]
    assert art_param.get_data().decode("utf-8").strip() == param_data
