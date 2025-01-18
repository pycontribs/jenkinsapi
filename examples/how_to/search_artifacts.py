"""
Search for job artifacts
"""

from __future__ import print_function
from jenkinsapi.api import search_artifacts

jenkinsurl = "http://localhost:8080"
jobid = "foo"
# I need a build that contains all of these
artifact_ids = ["test1.txt", "test2.txt"]
result = search_artifacts(jenkinsurl, jobid, artifact_ids)
print((repr(result)))
