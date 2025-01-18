"""
Example of using CrumbRequester - when CSRF protection is enabled in Jenkins
"""

from jenkinsapi.jenkins import Jenkins

jenkins = Jenkins(
    "http://localhost:8080",
    username="admin",
    password="password",
    use_crumb=True,
)

for job_name in jenkins.jobs:
    print(job_name)
