JenkinsAPI
==========

Jenkins is the market leading continuous integration system.

This API makes Jenkins even easier to use by providing an easy to use conventional Python interface.

Jenkins (and its predecessor Hudson) are fantastic projects - but they are somewhat Java-centric.

Thankfully the designers have provided an excellent and complete REST interface.

This library wraps up that interface as more conventional Python objects in order to make most Jenkins oriented tasks simpler.

This library can help you:

 * Query the test-results of a completed build
 * Get a objects representing the latest builds of a job
 * Search for artifacts by simple criteria
 * Block until jobs are complete
 * Install artifacts to custom-specified directory structures
 * Username/password auth support for jenkins instances with auth turned on
 * Search for builds by subversion revision
 * Add, remove and query jenkins slaves

Sections
========
.. toctree::
   :maxdepth: 2
   :titlesonly:

   getting_started
   readme_link
   examples
   low_level_examples
   module_reference
   project_info
   ../CONTRIBUTING
   Github <https://github.com/pycontribs/jenkinsapi>
   Documentation <http://pycontribs.github.io/jenkinsapi/>
   Releases <https://pypi.org/project/jenkinsapi/#history>

Important Links
---------------
* `Documentation <http://pycontribs.github.io/jenkinsapi>`__
* `Source Code <https://github.com/pycontribs/jenkinsapi>`_
* `Support and bug-reports <https://github.com/pycontribs/jenkinsapi/issues?direction=desc&sort=comments&state=open>`_
* `Releases <https://pypi.org/project/jenkinsapi/#history>`_

Installation
-------------

.. code-block:: bash

    pip install jenkinsapi

 * In Jenkins > 1.518 you will need to disable "Prevent Cross Site Request Forgery exploits".
 * Remember to set the Jenkins Location in general settings - Jenkins REST web-interface will not work if this is set incorrectly.

Examples
--------

JenkinsAPI is intended to map the objects in Jenkins (e.g. Builds, Views, Jobs) into easily managed Python objects

.. code-block:: python

   import jenkinsapi
   from jenkinsapi.jenkins import Jenkins
   J = Jenkins('http://localhost:8080')
   J.keys() # Jenkins objects appear to be dict-like, mapping keys (job-names) to ['foo', 'test_jenkinsapi']
   J['test_jenkinsapi'] # <jenkinsapi.job.Job test_jenkinsapi>
   J['test_jenkinsapi'].get_last_good_build() # <jenkinsapi.build.Build test_jenkinsapi #77>

JenkinsAPI lets you query the state of a running Jenkins server. It also allows you to change configuration and automate minor tasks on nodes and jobs.

You can use Jenkins to get information about recently completed builds. For example, you can get the revision number of the last successful build in order to trigger some kind of release process.

.. code-block:: python

    from jenkinsapi.jenkins import Jenkins

    def getSCMInfroFromLatestGoodBuild(url, jobName, username=None, password=None):
        J = Jenkins(url, username, password)
        job = J[jobName]
        lgb = job.get_last_good_build()
        return lgb.get_revision()

    if __name__ == '__main__':
        print(getSCMInfroFromLatestGoodBuild('http://localhost:8080', 'fooJob'))

When used with the Git source-control system line 20 will print out something like '8b4f4e6f6d0af609bb77f95d8fb82ff1ee2bba0d' - which looks suspiciously like a Git revision number.

Note: An API token can be specified instead of a real password when authenticating against Jenkins. Tokens can be generated from your user profile page under *Configure* > *API Token*.

Tips & Tricks
-------------

Getting the installed version of JenkinsAPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This package supports PEP-396 by implementing a version attribute. This contains a string in the format x.y.z:

.. code-block:: python

    import jenkinsapi
    print(jenkinsapi.__version__)



.. code-block:: bash

    jenkinsapi_version


Project Authors
===============

 * Salim Fadhley (sal@stodge.org)
 * Ramon van Alteren (ramon@vanalteren.nl)
 * Ruslan Lutsenko (ruslan.lutcenko@gmail.com)
 * Aleksey Maksimov
 * Clinton Steiner

Plus many others, please see the README file for a more complete list of contributors and how to contact them.

Extending and Improving JenkinsAPI
==================================

JenkinsAPI is a pure-Python project and can be improved with almost any programmer's text-editor or IDE. I'd recommend the following project layout which has been shown to work with both SublimeText2 and Eclipse/PyDev

 * Make sure that uv is installed on your computer.

 * Clone the project

.. code-block:: bash

    git clone https://github.com/pycontribs/jenkinsapi.git
    cd jenkinsapi

 * Install dependencies and run tests

.. code-block:: bash

    uv sync
    uv run pytest -sv --cov=jenkinsapi --cov-report=term-missing --cov-report=xml jenkinsapi_tests

Testing
-------

The project maintainers welcome any code-contributions. Please consider the following when you contribute code back to the project:

 * All contributions should come as github pull-requests. Please do not send code-snippets in email or as attachments to issues.
 * Please take a moment to clearly describe the intended goal of your pull-request.
 * Please ensure that any new feature is covered by a unit-test

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
