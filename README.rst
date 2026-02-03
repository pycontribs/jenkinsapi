Jenkinsapi
==========

.. image:: https://badge.fury.io/py/jenkinsapi.png
    :target: http://badge.fury.io/py/jenkinsapi

Installation
------------

.. code-block:: bash

    pip install jenkinsapi

Important Links
---------------
* `Documentation <http://pycontribs.github.io/jenkinsapi/>`__
* `Source Code <https://github.com/pycontribs/jenkinsapi>`_
* `Support and bug-reports <https://github.com/pycontribs/jenkinsapi/issues?direction=desc&sort=comments&state=open>`_
* `Releases <https://pypi.org/project/jenkinsapi/#history>`_


About this library
-------------------

Jenkins is the market leading continuous integration system.

Jenkins (and its predecessor Hudson) are useful projects for automating common development tasks (e.g. unit-testing, production batches) - but they are somewhat Java-centric.

Jenkinsapi makes scripting Jenkins tasks a breeze by wrapping the REST api into familiar python objects.

Here is a list of some of the most commonly used functionality

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

Full library capabilities are outlined in the `Documentation <http://pycontribs.github.io/jenkinsapi/>`__

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


Known issues
------------
* Job deletion operations fail unless Cross-Site scripting protection is disabled.

For other issues, please refer to the `support URL <https://github.com/pycontribs/jenkinsapi/issues?direction=desc&sort=comments&state=open>`_

Development
-----------

### Quick Start

1. Ensure astral uv and Docker are both installed on your local environment

.. code-block:: bash

    uv sync

2. Run tests

**Single-threaded:**

.. code-block:: bash

    make test

**Parallel (Recommended - uses 1/3 of CPU cores):**

.. code-block:: bash

    make test-parallel

**With coverage reporting:**

.. code-block:: bash

    make coverage-parallel

**Show calculated worker count:**

.. code-block:: bash

    make show-workers

### Using Docker for Testing (Recommended)

Jenkins can be started in Docker for testing, which is significantly faster than downloading and installing Jenkins.

**Requirements:**
- Docker installed and running

**Local Testing with Docker:**

.. code-block:: bash

    # Build the Docker image locally
    cd ci/
    docker build -t jenkinsapi-jenkins:local .

    # Run tests with Docker
    JENKINS_DOCKER_IMAGE=jenkinsapi-jenkins:local pytest -sv jenkinsapi_tests/systests/

**Using Pre-built Image from GitHub Container Registry:**

.. code-block:: bash

    # Tests will automatically pull the image if available
    pytest -sv jenkinsapi_tests/systests/

**Using War File (Fallback):**

If Docker is not available or you want to use the traditional approach:

.. code-block:: bash

    # Make sure Java is installed first
    SKIP_DOCKER=1 pytest -sv jenkinsapi_tests/systests/

For more detailed Docker setup and development instructions, see `ci/README.md <ci/README.md>`_

### Make Targets

The project uses a Makefile for common operations:

**Testing:**

.. code-block:: bash

    make test              # Run tests single-threaded
    make test-parallel     # Run tests with 1/3 CPU workers (recommended)
    make coverage-parallel # Run tests with coverage and parallel workers
    make show-workers      # Display calculated worker count

**Docker:**

.. code-block:: bash

    make docker-build      # Build Docker image locally
    make docker-publish    # Build and publish Docker image

**Plugin Management:**

.. code-block:: bash

    make update-plugins    # Check for and apply Jenkins plugin updates

**Other:**

.. code-block:: bash

    make lint              # Run code linting
    make dist              # Build distribution package
    make clean             # Clean temporary files

### Parallel Test Execution

Tests are optimized to run in parallel using pytest-xdist. The number of workers is dynamically calculated as **1/3 of available CPU cores** (minimum 1).

**Benefits:**
- Faster test execution (typically 60-70% faster on multi-core systems)
- Automatic scaling based on available hardware
- Conservative resource usage to prevent system overload

**Accessing executor information in tests:**

.. code-block:: python

    def test_example(jenkins, executor_id):
        """Test that knows which executor it's running on."""
        print(f"Running on executor: {executor_id}")
        # executor_id will be 'gw0', 'gw1', etc. with -n flag, or 'local' single-threaded
        assert jenkins is not None

### Automatic Plugin Updates

The project includes automated Jenkins plugin management:

1. **Daily Plugin Update Checks** (``.github/workflows/update-jenkins-plugins.yml``)
   - Runs daily and checks for available plugin updates
   - Creates pull requests with updated versions
   - Updates ci/plugins.txt with new plugin versions

2. **Daily Docker Image Builds** (``.github/workflows/build-jenkins-image.yml``)
   - Runs daily at 2 AM UTC
   - Builds Docker image with current plugins
   - Runs full test suite before publishing (prevents broken images)
   - Publishes to GitHub Container Registry (ghcr.io)

3. **Plugin Optimization**
   - Removed UI-only plugins: bootstrap5-api, echarts-api, font-awesome-api, ionicons-api, prism-api, antisamy-markup-formatter
   - Image size reduced by ~11% (6 plugins removed)
   - 47 essential plugins pinned to specific versions
   - Uses jenkins-plugin-cli with --latest=false to respect version pins

Python versions
---------------

The project has been tested against Python versions:

* 3.9 - 3.14

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
