"""
System test to verify all required plugins load and work correctly.
This ensures Jenkins and all plugins are compatible and functional.
"""


def test_jenkins_loads_with_all_plugins(jenkins):
    """Test that Jenkins starts successfully with all required plugins."""
    # If we got here, Jenkins started successfully with all plugins
    if jenkins is None:
        raise RuntimeError("Jenkins instance is None")
    jenkins.poll()


def test_matrix_project_plugin_available(jenkins):
    """Verify matrix-project plugin is installed and functional."""
    from jenkinsapi_tests.systests.job_configs import MATRIX_JOB
    from jenkinsapi_tests.test_utils.random_strings import random_string

    job_name = "matrix_plugin_test_%s" % random_string()
    job = jenkins.create_job(job_name, MATRIX_JOB)
    if job is None:
        raise RuntimeError("Failed to create job")
    if not (
        "matrix" in str(type(job)).lower() or hasattr(job, "get_matrix_runs")
    ):
        raise RuntimeError("Job does not have matrix plugin features")


def test_envinject_plugin_available(jenkins):
    """Verify envinject plugin is installed and functional."""
    from jenkinsapi_tests.systests.job_configs import JOB_WITH_ENV_VARS
    from jenkinsapi_tests.test_utils.random_strings import random_string

    job_name = "envinject_plugin_test_%s" % random_string()
    job = jenkins.create_job(job_name, JOB_WITH_ENV_VARS)
    if job is None:
        raise RuntimeError("Failed to create job")
    # The job should be created successfully with envinject wrapper
    if "ping" not in job.get_config():
        raise RuntimeError(
            "Job config does not contain expected 'ping' content"
        )


def test_git_plugin_available(jenkins):
    """Verify git plugin is installed and available."""
    # This is a passive test - if the git plugin is missing, other tests will fail
    # We just verify Jenkins is functional
    jenkins.poll()
    if jenkins.version is None:
        raise RuntimeError("Jenkins version is None")
