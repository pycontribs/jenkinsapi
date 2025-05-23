Getting Started
===============

JenkinsAPI lets you query the state of a running Jenkins server. It also allows you to change configuration and automate minor tasks on nodes and jobs.

Installation
-------------

.. code-block:: bash

	pip install jenkinsapi

Example
-------

JenkinsAPI is intended to map the objects in Jenkins (e.g. Builds, Views, Jobs) into easily managed Python objects:

.. code-block:: python

	from jenkinsapi.jenkins import Jenkins
	J = Jenkins('http://localhost:8080')
	print(J.version) # 1.542
	print(J.keys()) # foo, test_jenkinsapi
	print(J.get('test_jenkinsapi')) # <jenkinsapi.job.Job test_jenkinsapi>
	print(J.get('test_jenkinsapi').get_last_good_build()) # <jenkinsapi.build.Build test_jenkinsapi #77>

Testing
-------

If you have installed the test dependencies on your system already, you can run
the testsuite with the following command:

.. code-block:: bash

    uv sync
    uv run pytest -sv --cov=jenkinsapi --cov-report=term-missing --cov-report=xml jenkinsapi_tests

Otherwise using a virtualenv is recommended. Setuptools will automatically fetch
missing test dependencies:

.. code-block:: bash

    uv venv
    uv python install
    uv run pytest -sv --cov=jenkinsapi --cov-report=term-missing --cov-report=xml jenkinsapi_tests

Get version of Jenkins
----------------------

.. code-block:: python

    from jenkinsapi.jenkins import Jenkins

    def get_server_instance():
        jenkins_url = 'http://jenkins_host:8080'
        server = Jenkins(jenkins_url, username='foouser', password='foopassword')
        return server

    if __name__ == '__main__':
        print get_server_instance().version

The above code prints version of Jenkins running on the host *jenkins_host*.

From Jenkins vesion 1.426 onward one can specify an API token instead of your real password while authenticating the user against Jenkins instance.

Refer to the the Jenkis wiki page `Authenticating scripted clients <https://wiki.jenkins-ci.org/display/JENKINS/Authenticating+scripted+clients>`_ for details about how a user can generate an API token.

Once you have API token you can pass the API token instead of real password while creating an Jenkins server instance using Jenkins API.

Get details of jobs running on Jenkins server
---------------------------------------------

.. code-block:: python

    """Get job details of each job that is running on the Jenkins instance"""
    def get_job_details():
        # Refer Example #1 for definition of function 'get_server_instance'
        server = get_server_instance()
        for job_name, job_instance in server.get_jobs():
            print 'Job Name:%s' % (job_instance.name)
            print 'Job Description:%s' % (job_instance.get_description())
            print 'Is Job running:%s' % (job_instance.is_running())
            print 'Is Job enabled:%s' % (job_instance.is_enabled())

Disable/Enable a Jenkins Job
----------------------------

.. code-block:: python

    def disable_job():
        """Disable a Jenkins job"""
        # Refer Example #1 for definition of function 'get_server_instance'
        server = get_server_instance()
        job_name = 'nightly-build-job'
        if (server.has_job(job_name)):
            job_instance = server.get_job(job_name)
            job_instance.disable()
            print 'Name:%s,Is Job Enabled ?:%s' % (job_name,job_instance.is_enabled())

Use the call ``job_instance.enable()`` to enable a Jenkins Job.

Get Plugin details
------------------

Below chunk of code gets the details of the plugins currently installed in the
Jenkins instance.

.. code-block:: python

    def get_plugin_details():
        # Refer Example #1 for definition of function 'get_server_instance'
        server = get_server_instance()
        for plugin in server.get_plugins().values():
            print "Short Name:%s" % (plugin.shortName)
            print "Long Name:%s" % (plugin.longName)
            print "Version:%s" % (plugin.version)
            print "URL:%s" % (plugin.url)
            print "Active:%s" % (plugin.active)
            print "Enabled:%s" % (plugin.enabled)

Getting version information from a completed build
--------------------------------------------------

This is a typical use of JenkinsAPI - it was the very first use I had in mind when the project was first built.

In a continuous-integration environment you want to be able to programatically detect the version-control information of the last succsessful build in order to trigger some kind of release process.

.. code-block:: python

    from jenkinsapi.jenkins import Jenkins

    def getSCMInfroFromLatestGoodBuild(url, jobName, username=None, password=None):
        J = Jenkins(url, username, password)
        job = J[jobName]
        lgb = job.get_last_good_build()
        return lgb.get_revision()

    if __name__ == '__main__':
        print getSCMInfroFromLatestGoodBuild('http://localhost:8080', 'fooJob')

When used with the Git source-control system line 20 will print out something like '8b4f4e6f6d0af609bb77f95d8fb82ff1ee2bba0d' - which looks suspiciously like a Git revision number.
