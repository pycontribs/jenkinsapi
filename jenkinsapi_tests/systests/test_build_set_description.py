"""
System tests for Build.set_description().
"""

import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import SHORTISH_JOB

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def test_set_description(jenkins):
    job_name = "desc_%s" % random_string()
    job = jenkins.create_job(job_name, SHORTISH_JOB)
    qq = job.invoke()
    qq.block_until_building()
    build = qq.get_build()
    build.block_until_complete()

    build.set_description("my test description")
    build.poll()
    assert build.get_description() == "my test description"
