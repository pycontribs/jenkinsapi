"""
System tests for `jenkinsapi.jenkins` module.
"""

import time

from jenkinsapi_tests.systests.job_configs import JOB_WITH_ENV_VARS
from jenkinsapi_tests.test_utils.random_strings import random_string


def test_get_env_vars(jenkins):
    job_name = "get_env_vars_create1_%s" % random_string()
    job = jenkins.create_job(job_name, JOB_WITH_ENV_VARS)
    job.invoke(block=True)
    build = job.get_last_build()
    while build.is_running():
        time.sleep(0.25)

    # Poll for environment variables with exponential backoff
    # Jenkins takes variable time to write injected env vars to API
    max_retries = 20
    retry_delay = 0.5
    last_error = None
    for attempt in range(max_retries):
        try:
            data = build.get_env_vars()
            assert data["key1"] == "value1"
            assert data["key2"] == "value2"
            return
        except (KeyError, Exception) as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error
