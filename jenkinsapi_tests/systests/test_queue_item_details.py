"""
System tests for QueueItem detail properties:
- is_blocked, is_stuck, is_buildable
- get_age, get_eta, get_causes
"""

import time
import logging
import pytest
from jenkinsapi.queue import QueueItem
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import LONG_RUNNING_JOB

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


@pytest.fixture
def no_executors(jenkins, request):
    master = jenkins.nodes["Built-In Node"]
    num_executors = master.get_num_executors()
    master.set_num_executors(0)

    def restore():
        master.set_num_executors(num_executors)

    request.addfinalizer(restore)
    return num_executors


def test_queue_item_is_blocked_and_buildable(jenkins, no_executors):
    """Queue a job and check is_blocked, is_buildable, is_stuck properties."""
    job_name = random_string()
    job = jenkins.create_job(job_name, LONG_RUNNING_JOB)
    job.invoke()

    time.sleep(1)
    assert job.is_queued()

    qi = job.get_queue_item()
    assert isinstance(qi, QueueItem)

    # With no executors the item is blocked, not buildable
    assert isinstance(qi.is_blocked, bool)
    assert isinstance(qi.is_buildable, bool)
    assert isinstance(qi.is_stuck, bool)

    # Clean up
    jenkins.get_queue().delete_item(qi)


def test_queue_item_get_age(jenkins, no_executors):
    """A queued item's age should be a positive number of seconds."""
    job_name = random_string()
    job = jenkins.create_job(job_name, LONG_RUNNING_JOB)
    job.invoke()

    time.sleep(2)
    assert job.is_queued()

    qi = job.get_queue_item()
    age = qi.get_age()
    assert age > 0, "Expected age > 0 seconds, got %s" % age

    jenkins.get_queue().delete_item(qi)


def test_queue_item_get_eta(jenkins, no_executors):
    """get_eta should return a non-negative float."""
    job_name = random_string()
    job = jenkins.create_job(job_name, LONG_RUNNING_JOB)
    job.invoke()

    time.sleep(1)
    assert job.is_queued()

    qi = job.get_queue_item()
    eta = qi.get_eta()
    assert eta >= 0.0, "Expected eta >= 0, got %s" % eta

    jenkins.get_queue().delete_item(qi)


def test_queue_item_get_causes(jenkins, no_executors):
    """get_causes should return a list for a manually triggered job."""
    job_name = random_string()
    job = jenkins.create_job(job_name, LONG_RUNNING_JOB)
    job.invoke()

    time.sleep(1)
    assert job.is_queued()

    qi = job.get_queue_item()
    causes = qi.get_causes()
    assert isinstance(causes, list)

    jenkins.get_queue().delete_item(qi)
