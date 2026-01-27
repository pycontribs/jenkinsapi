"""
System tests for `jenkinsapi.jenkins` module.
"""

import time
import logging
import pytest
from jenkinsapi.custom_exceptions import NoBuildData

log = logging.getLogger(__name__)

JOB_CONFIGS = {
    "A": """<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers>
    <hudson.tasks.BuildTrigger>
      <childProjects>B</childProjects>
      <threshold>
        <name>SUCCESS</name>
        <ordinal>0</ordinal>
        <color>BLUE</color>
      </threshold>
    </hudson.tasks.BuildTrigger>
  </publishers>
  <buildWrappers/>
</project>""",
    "B": """<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers>
    <hudson.tasks.BuildTrigger>
      <childProjects>C</childProjects>
      <threshold>
        <name>SUCCESS</name>
        <ordinal>0</ordinal>
        <color>BLUE</color>
      </threshold>
    </hudson.tasks.BuildTrigger>
  </publishers>
  <buildWrappers/>
</project>""",
    "C": """<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>""",
}

DELAY = 10


def test_stream_relationship(jenkins):
    """
    Can we keep track of the relationships between upstream & downstream jobs?
    """
    # Retry entire test with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            for job_name, job_config in JOB_CONFIGS.items():
                jenkins.create_job(job_name, job_config)

            time.sleep(1)

            jenkins["A"].invoke()

            for _ in range(10):
                try:
                    jenkins["C"].get_last_completed_buildnumber() > 0
                except NoBuildData:
                    log.info(
                        "Waiting %i seconds for until the final job has run",
                        DELAY,
                    )
                    time.sleep(DELAY)
                else:
                    break
            else:
                pytest.fail("Jenkins took too long to run these jobs")

            assert jenkins["C"].get_upstream_jobs() == [jenkins["B"]]
            assert jenkins["B"].get_upstream_jobs() == [jenkins["A"]]

            assert jenkins["A"].get_downstream_jobs() == [jenkins["B"]]
            assert jenkins["B"].get_downstream_jobs() == [jenkins["C"]]
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error
