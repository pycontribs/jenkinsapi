"""
System tests for job build configuration options ported from jenkins_api_client:
- Job.set_concurrent_builds
- Job.block_build_when_downstream_building / unblock_build_when_downstream_building
- Job.block_build_when_upstream_building / unblock_build_when_upstream_building
- Job.restrict_to_node
"""

import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import EMPTY_JOB

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def test_set_concurrent_builds_enable(jenkins):
    """Enable concurrent builds and verify the config is updated."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    job.set_concurrent_builds(True)

    config = job.get_config()
    assert "<concurrentBuild>true</concurrentBuild>" in config


def test_set_concurrent_builds_disable(jenkins):
    """Disable concurrent builds after enabling and verify the config."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    job.set_concurrent_builds(True)
    job.set_concurrent_builds(False)

    config = job.get_config()
    assert "<concurrentBuild>false</concurrentBuild>" in config


def test_block_build_when_downstream_building(jenkins):
    """Block builds when downstream is building and verify config."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    job.block_build_when_downstream_building()

    config = job.get_config()
    assert (
        "<blockBuildWhenDownstreamBuilding>true</blockBuildWhenDownstreamBuilding>"
        in config
    )


def test_unblock_build_when_downstream_building(jenkins):
    """Unblock downstream building block and verify config."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    job.block_build_when_downstream_building()
    job.unblock_build_when_downstream_building()

    config = job.get_config()
    assert (
        "<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>"
        in config
    )


def test_block_build_when_upstream_building(jenkins):
    """Block builds when upstream is building and verify config."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    job.block_build_when_upstream_building()

    config = job.get_config()
    assert (
        "<blockBuildWhenUpstreamBuilding>true</blockBuildWhenUpstreamBuilding>"
        in config
    )


def test_unblock_build_when_upstream_building(jenkins):
    """Unblock upstream building block and verify config."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    job.block_build_when_upstream_building()
    job.unblock_build_when_upstream_building()

    config = job.get_config()
    assert (
        "<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>"
        in config
    )


def test_restrict_to_node(jenkins):
    """Restrict job to a specific node label and verify config."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    job.restrict_to_node("my-agent")

    config = job.get_config()
    assert "<assignedNode>my-agent</assignedNode>" in config
    assert "<canRoam>false</canRoam>" in config


def test_restrict_to_node_update(jenkins):
    """Re-restrict a job to a different node and verify config is updated."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    job.restrict_to_node("agent-1")
    job.restrict_to_node("agent-2")

    config = job.get_config()
    assert "<assignedNode>agent-2</assignedNode>" in config
    assert "<assignedNode>agent-1</assignedNode>" not in config
