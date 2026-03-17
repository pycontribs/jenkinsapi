"""
System tests for `jenkinsapi.jenkins` module.
"""

import time
import logging
from jenkinsapi_tests.systests.job_configs import LONG_RUNNING_JOB
from jenkinsapi_tests.test_utils.random_strings import random_string

log = logging.getLogger(__name__)


def test_get_executors(jenkins):
    # Retry entire test with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            node_name = random_string()
            node_dict = {
                "num_executors": 2,
                "node_description": "Test JNLP Node",
                "remote_fs": "/tmp",
                "labels": "systest_jnlp",
                "exclusive": True,
            }
            jenkins.nodes.create_node(node_name, node_dict)

            executors = jenkins.get_executors(node_name)
            assert executors.count == 2

            for count, execs in enumerate(executors):
                assert count == execs.get_number()
                assert execs.is_idle() is True
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error


def test_running_executor(jenkins):
    # Retry entire test with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            node_name = random_string()
            node_dict = {
                "num_executors": 1,
                "node_description": "Test JNLP Node",
                "remote_fs": "/tmp",
                "labels": "systest_jnlp",
                "exclusive": True,
            }
            jenkins.nodes.create_node(node_name, node_dict)
            job_name = "create_%s" % random_string()
            job = jenkins.create_job(job_name, LONG_RUNNING_JOB)
            qq = job.invoke()
            qq.block_until_building()

            if job.is_running() is False:
                time.sleep(1)

            executors = jenkins.get_executors(node_name)
            all_idle = True
            for execs in executors:
                if execs.is_idle() is False:
                    all_idle = False
                    assert execs.get_progress() != -1
                    assert (
                        execs.get_current_executable() == qq.get_build_number()
                    )
                    assert execs.likely_stuck() is False
            assert all_idle is True, "Executor should have been triggered."
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error


def test_idle_executors(jenkins):
    # Retry entire test with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            node_name = random_string()
            node_dict = {
                "num_executors": 1,
                "node_description": "Test JNLP Node",
                "remote_fs": "/tmp",
                "labels": "systest_jnlp",
                "exclusive": True,
            }
            jenkins.nodes.create_node(node_name, node_dict)

            executors = jenkins.get_executors(node_name)

            for execs in executors:
                assert execs.get_progress() == -1
                assert execs.get_current_executable() is None
                assert execs.likely_stuck() is False
                assert execs.is_idle() is True
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error
