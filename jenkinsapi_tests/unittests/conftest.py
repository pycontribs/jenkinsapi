"""Pytest configuration for unit tests with Docker support.

This module provides shared fixtures and configuration for running unit tests
with optional Docker-based Jenkins support.
"""

import os
import pytest
import logging

log = logging.getLogger(__name__)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "docker: mark test as requiring Docker Jenkins (integration test)",
    )
    config.addinivalue_line(
        "markers",
        "requires_docker: mark test as requiring Docker to be available",
    )
    config.addinivalue_line(
        "markers", "unit: mark test as pure unit test (no Docker needed)"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their module or markers."""
    for item in items:
        # Auto-mark pure unit tests if they don't have markers
        if not any(
            marker.name in ("docker", "unit") for marker in item.iter_markers()
        ):
            item.add_marker(pytest.mark.unit)


@pytest.fixture(scope="session")
def docker_available():
    """Check if Docker is available in the environment."""
    from jenkinsapi.utils.jenkins_launcher import JenkinsLancher

    available = JenkinsLancher._has_docker()
    if available:
        log.info("Docker is available for testing")
    else:
        log.info("Docker is not available for testing")
    return available


@pytest.fixture(scope="session")
def skip_docker_env(docker_available):
    """Determine if Docker should be skipped based on environment."""
    skip_docker = os.getenv("SKIP_DOCKER", "").lower() in ("1", "true")
    return skip_docker or not docker_available


@pytest.fixture(scope="session")
def docker_image():
    """Get the Docker image to use for testing."""
    return os.getenv(
        "JENKINS_DOCKER_IMAGE",
        "ghcr.io/pycontribs/jenkinsapi-jenkins:latest",
    )


@pytest.fixture(scope="session")
def test_mode():
    """Determine which test mode to use.

    Returns:
        str: One of 'docker', 'war', or 'external'
    """
    from jenkinsapi.utils.jenkins_launcher import JenkinsLancher

    if "JENKINS_URL" in os.environ:
        return "external"
    elif os.getenv("SKIP_DOCKER", "").lower() in ("1", "true"):
        return "war"
    elif JenkinsLancher._has_docker():
        return "docker"
    else:
        return "war"


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration information."""
    return {
        "docker_enabled": os.getenv("JENKINS_DOCKER_IMAGE", "") != "",
        "skip_docker": os.getenv("SKIP_DOCKER", "").lower() in ("1", "true"),
        "external_jenkins_url": os.getenv("JENKINS_URL"),
        "use_docker_by_default": os.getenv(
            "JENKINS_DOCKER_IMAGE",
            "ghcr.io/pycontribs/jenkinsapi-jenkins:latest",
        ),
    }


def pytest_runtest_setup(item):
    """Configure test execution based on markers and environment."""
    # Skip Docker tests if Docker is not available
    if "docker" in item.keywords:
        from jenkinsapi.utils.jenkins_launcher import JenkinsLancher

        if not JenkinsLancher._has_docker():
            pytest.skip("Docker not available")

        skip_docker = os.getenv("SKIP_DOCKER", "").lower() in ("1", "true")
        if skip_docker:
            pytest.skip("Docker tests skipped (SKIP_DOCKER=1)")
