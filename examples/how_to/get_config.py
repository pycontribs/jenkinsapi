"""
An example of how to use JenkinsAPI to fetch the config XML of a job.
"""

from __future__ import print_function
from jenkinsapi.jenkins import Jenkins

jenkins = Jenkins("http://localhost:8080")
jobName = jenkins.keys()[0]  # get the first job

config = jenkins[jobName].get_config()

print(config)
