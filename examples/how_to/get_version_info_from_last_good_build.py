"""
Extract version information from the latest build.
"""

from jenkinsapi.jenkins import Jenkins


job_name = "foo"
jenkins = Jenkins("http://localhost:8080")
job = jenkins[job_name]
lgb = job.get_last_good_build()
print(lgb.get_revision())
