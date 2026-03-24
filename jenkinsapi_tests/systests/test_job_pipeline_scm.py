"""
Tests for pipeline job SCM handling (issue #891).

These tests validate that SCM elements are correctly detected in pipeline jobs,
where SCM configuration is nested under 'definition/scm' rather than at the
root level like in traditional freestyle jobs.
"""

import pytest
import requests

from jenkinsapi.custom_exceptions import NotSupportSCM, NotConfiguredSCM
from jenkinsapi_tests.systests.job_configs import (
    PIPELINE_SCM_CONFIG,
    PIPELINE_SCM_JOB,
)
from jenkinsapi_tests.test_utils.random_strings import random_string


def test_pipeline_job_with_git_scm(jenkins):
    """Pipeline job SCM type and URL can be extracted (issue #891)."""
    job_name = random_string()
    job = jenkins.create_job(job_name, PIPELINE_SCM_JOB)

    # Verify SCM type is correctly identified
    assert job.get_scm_type() == job._scm_map[PIPELINE_SCM_CONFIG["scm_class"]]

    # Verify SCM URL is correctly extracted
    assert job.get_scm_url()[0] == PIPELINE_SCM_CONFIG["git_url"]


def test_pipeline_job_scm_prefix_set(jenkins):
    """Pipeline job SCM detection sets correct prefix for nested location."""
    job_name = random_string()
    job = jenkins.create_job(job_name, PIPELINE_SCM_JOB)

    # Verify the SCM prefix is set to the pipeline definition location
    job.get_scm_type()  # This triggers the SCM element discovery
    assert job._scm_prefix == "definition/"


def test_pipeline_job_with_null_scm_raises_error(jenkins):
    """Pipeline job with NullSCM should raise NotConfiguredSCM."""
    pipeline_no_scm = """<?xml version='1.1' encoding='UTF-8'?>
<flow-definition>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition">
    <scm class="hudson.scm.NullSCM"/>
  </definition>
</flow-definition>"""

    job_name = random_string()
    job = jenkins.create_job(job_name, pipeline_no_scm)

    with pytest.raises(NotConfiguredSCM):
        job.get_scm_type()


def test_pipeline_job_with_unsupported_scm_raises_error(jenkins):
    """Pipeline job with unsupported SCM class should raise NotSupportSCM."""
    pipeline_unsupported_scm = """<?xml version='1.1' encoding='UTF-8'?>
<flow-definition>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition">
    <scm class="com.example.UnsupportedSCM"/>
  </definition>
</flow-definition>"""

    job_name = random_string()
    job = jenkins.create_job(job_name, pipeline_unsupported_scm)

    with pytest.raises(NotSupportSCM):
        job.get_scm_type()
