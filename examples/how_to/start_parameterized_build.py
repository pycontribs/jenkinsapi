"""
Start a Parameterized Build
"""

from __future__ import print_function

from jenkinsapi.jenkins import Jenkins

jenkins = Jenkins("http://localhost:8080")

params = {"VERSION": "1.2.3", "PYTHON_VER": "2.7"}

# This will start the job in non-blocking manner
jenkins.build_job("foo", params)


# This will start the job and will return a QueueItem object which
# can be used to get build results
job = jenkins["foo"]
qi = job.invoke(build_params=params)

# Block this script until build is finished
if qi.is_queued() or qi.is_running():
    qi.block_until_complete()

build = qi.get_build()
print(build)
