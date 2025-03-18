jenkinsapi
==========

.. image:: https://badge.fury.io/py/jenkinsapi.png
    :target: http://badge.fury.io/py/jenkinsapi

.. image:: https://codecov.io/gh/pycontribs/jenkinsapi/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/pycontribs/jenkinsapi

About this library
-------------------

Jenkins is the market leading continuous integration system, originally created by Kohsuke Kawaguchi.

Jenkins (and its predecessor Hudson) are useful projects for automating common development tasks (e.g. unit-testing, production batches) - but they are somewhat Java-centric.
| Jenkinsapi makes scripting Jenkins tasks a breeze by wrapping the REST api into familiar python objects.
| Here is a list of some of the most commonly used functionality

* Add, remove, and query Jenkins jobs
* Control pipeline execution
    * Query the results of a completed build
    * Block until jobs are complete or run jobs asyncronously
    * Get objects representing the latest builds of a job
* Artifact management
    * Search for artifacts by simple criteria
    * Install artifacts to custom-specified directory structures
* Search for builds by source code revision
* Create, destroy, and monitor
    * Build nodes (Webstart and SSH slaves)
    * Views (including nested views using NestedViews Jenkins plugin)
    * Credentials (username/password and ssh key)
* Authentication support for username and password
* Manage jenkins and plugin installation

Full library capabilities are outlined in the `Documentation <http://jenkinsapi.readthedocs.io/en/latest/index.html>`__


Known issues
------------
* Job deletion operations fail unless Cross-Site scripting protection is disabled.

For other issues, please refer to the `support URL <https://github.com/pycontribs/jenkinsapi/issues?direction=desc&sort=comments&state=open>`_

Important Links
---------------
* `Support and bug-reports <https://github.com/pycontribs/jenkinsapi/issues?direction=desc&sort=comments&state=open>`_
* `Source Code <https://github.com/pycontribs/jenkinsapi>`_
* `Documentation <https://jenkinsapi.readthedocs.org/en/latest/>`__
* `Releases <http://pypi.python.org/pypi/jenkinsapi>`_

Installation
-------------

Egg-files for this project are hosted on PyPi. Most Python users should be able to use pip or setuptools to automatically install this project.

Using Pip or Setuptools
^^^^^^^^^^^^^^^^^^^^^^^

Most users can do the following:

.. code-block:: bash

	pip install jenkinsapi

Or:

.. code-block:: bash

	easy_install jenkinsapi

Both of these techniques can be combined with virtualenv to create an application-specific installation.

Using your operating-system's package manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ubuntu users can now use apt to install this package:

.. code-block:: bash

    apt-get install python-jenkinsapi

Beware that this technique will get a somewhat older version of Jenkinsapi.

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

More examples available on `Github <https://github.com/pycontribs/jenkinsapi/tree/master/examples>`_

Testing
-------

If you have installed the test dependencies on your system already, you can run
the testsuite with the following command:

.. code-block:: bash

    uv python sync
    uv run pytest -sv --cov=jenkinsapi --cov-report=term-missing --cov-report=xml jenkinsapi_tests

Otherwise using a virtualenv is recommended. Setuptools will automatically fetch
missing test dependencies:

.. code-block:: bash

    uv venv
    uv python install
    uv run pytest -sv --cov=jenkinsapi --cov-report=term-missing --cov-report=xml jenkinsapi_tests

Development
-----------

* Make sure that you have Java_ installed. Jenkins will be automatically
  downloaded and started during tests.
* Create virtual environment for development
* Install package in development mode

.. code-block:: bash

    uv sync

* Make your changes, write tests and check your code

.. code-block:: bash

    uv run pytest -sv

Python versions
---------------

The project has been tested against Python versions:

* 3.8 - 3.13

Jenkins versions
----------------

Project tested on both stable (LTS) and latest Jenkins versions.

Project Contributors
--------------------

* Aleksey Maksimov (ctpeko3a@gmail.com)
* Salim Fadhley (sal@stodge.org)
* Ramon van Alteren (ramon@vanalteren.nl)
* Ruslan Lutsenko (ruslan.lutcenko@gmail.com)
* Cleber J Santos (cleber@simplesconsultoria.com.br)
* William Zhang (jollychang@douban.com)
* Victor Garcia (bravejolie@gmail.com)
* Bradley Harris (bradley@ninelb.com)
* Kyle Rockman (kyle.rockman@mac.com)
* Sascha Peilicke (saschpe@gmx.de)
* David Johansen (david@makewhat.is)
* Misha Behersky (bmwant@gmail.com)
* Clinton Steiner (clintonsteiner@gmail.com)

Please do not contact these contributors directly for support questions! Use the GitHub tracker instead.

.. _Java: https://www.oracle.com/java/technologies/downloads/#java17
