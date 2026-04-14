"""
System tests for job/folder credentials property (issue #802).

Tests verifying that Job objects have a credentials property that
constructs the folder credentials URL and returns a Credentials2x instance.
This provides access to folder-scoped credentials without requiring
the workaround mentioned in issue #802.
"""

import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.test_utils.retry import retry
from jenkinsapi_tests.systests.job_configs import EMPTY_JOB
from jenkinsapi.credentials import Credentials2x
from jenkinsapi.job import Job

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


@retry()
def test_job_credentials_property_accessible(jenkins):
    """
    Test that Job.credentials property is accessible.

    This test verifies the credentials property can be accessed without
    errors. Whether credentials actually exist at that location depends
    on the Jenkins configuration and available plugins.
    """
    job_name = "job_%s" % random_string()
    jenkins.create_job(job_name, EMPTY_JOB)
    jenkins.poll()
    job = jenkins[job_name]

    # The credentials property should be accessible
    assert hasattr(job, "credentials")
    # And it should return a Credentials2x instance
    credentials = job.credentials
    assert isinstance(credentials, Credentials2x)


@retry()
def test_job_credentials_url_construction(jenkins):
    """
    Test that Job.credentials constructs the correct folder credentials URL.

    The URL pattern for folder credentials should follow:
    {job_url}/credentials/store/folder/domain/_/
    """
    job_name = "job_%s" % random_string()
    jenkins.create_job(job_name, EMPTY_JOB)
    jenkins.poll()
    job = jenkins[job_name]

    credentials = job.credentials
    # Construct the expected URL
    expected_url = (
        "http://localhost:8080/job/%s/credentials/store/folder/domain/_"
        % job_name
    )
    # Verify the baseurl matches (note: JenkinsBase may strip trailing slashes)
    assert credentials.baseurl == expected_url


@retry()
def test_credentials_property_is_credentials2x_instance(jenkins):
    """
    Test that Job.credentials returns a Credentials2x instance.

    This ensures the correct credentials class is used for accessing
    folder-scoped credentials.
    """
    job_name = "job_%s" % random_string()
    jenkins.create_job(job_name, EMPTY_JOB)
    jenkins.poll()
    job = jenkins[job_name]

    credentials = job.credentials

    # Verify it's a Credentials2x instance
    assert isinstance(credentials, Credentials2x)
    # Verify it has the expected methods
    assert hasattr(credentials, "keys")
    assert hasattr(credentials, "__getitem__")
    assert hasattr(credentials, "__setitem__")
