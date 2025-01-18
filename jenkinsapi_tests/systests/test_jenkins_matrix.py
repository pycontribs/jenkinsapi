"""
System tests for `jenkinsapi.jenkins` module.
"""

import re
import time
from jenkinsapi_tests.systests.job_configs import MATRIX_JOB
from jenkinsapi_tests.test_utils.random_strings import random_string


def test_invoke_matrix_job(jenkins):
    job_name = "create_%s" % random_string()
    job = jenkins.create_job(job_name, MATRIX_JOB)
    queueItem = job.invoke()
    queueItem.block_until_complete()

    build = job.get_last_build()

    while build.is_running():
        time.sleep(1)

    set_of_groups = set()
    for run in build.get_matrix_runs():
        assert run.get_number() == build.get_number()
        assert run.get_upstream_build() == build
        match_result = re.search("\xbb (.*) #\\d+$", run.name)
        assert match_result is not None
        set_of_groups.add(match_result.group(1))
        build.get_master_job_name()

    assert set_of_groups == set(["one", "two", "three"])
