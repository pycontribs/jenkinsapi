"""
How to get build from job and query that build
"""

from __future__ import print_function
from jenkinsapi.jenkins import Jenkins


jenkins = Jenkins("http://localhost:8080")
# Print all jobs in Jenkins
print(jenkins.items())

job = jenkins.get_job("foo")
build = job.get_last_build()
print(build)

mjn = build.get_master_job_name()
print(mjn)
