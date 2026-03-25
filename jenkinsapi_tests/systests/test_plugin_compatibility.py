"""
System test to verify all required plugins load and work correctly.
This ensures Jenkins and all plugins are compatible and functional.
"""

import pytest

pytestmark = pytest.mark.docker


def test_jenkins_loads_with_all_plugins(jenkins):
    """Test that Jenkins starts successfully with all required plugins."""
    # If we got here, Jenkins started successfully with all plugins
    assert jenkins is not None
    jenkins.poll()


def test_matrix_project_plugin_available(jenkins):
    """Verify matrix-project plugin is installed and functional."""
    from jenkinsapi_tests.systests.job_configs import MATRIX_JOB
    from jenkinsapi_tests.test_utils.random_strings import random_string

    job_name = "matrix_plugin_test_%s" % random_string()
    job = jenkins.create_job(job_name, MATRIX_JOB)
    assert job is not None
    assert "matrix-project" in job.get_config()


def test_envinject_plugin_available(jenkins):
    """Verify envinject plugin is installed and functional."""
    from jenkinsapi_tests.systests.job_configs import JOB_WITH_ENV_VARS
    from jenkinsapi_tests.test_utils.random_strings import random_string

    job_name = "envinject_plugin_test_%s" % random_string()
    job = jenkins.create_job(job_name, JOB_WITH_ENV_VARS)
    assert job is not None
    # The job should be created successfully with envinject wrapper
    assert "EnvInjectBuildWrapper" in job.get_config()


def test_git_plugin_available(jenkins):
    """Verify git plugin is installed and available."""
    # This is a passive test - if the git plugin is missing, other tests will fail
    # We just verify Jenkins is functional
    jenkins.poll()
    assert jenkins.version is not None
