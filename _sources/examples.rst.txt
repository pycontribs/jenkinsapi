How to use JenkinsAPI
=====================

Add new command to "Shell" build step
--------------------------------------------

.. code-block:: python

    import xml.etree.ElementTree as et
    from jenkinsapi.jenkins import Jenkins

    J = Jenkins("http://localhost:8080")
    EMPTY_JOB_CONFIG = """
    <?xml version='1.0' encoding='UTF-8'?>
    <project>
      <actions>jkkjjk</actions>
      <description></description>
      <keepDependencies>false</keepDependencies>
      <properties/>
      <scm class="hudson.scm.NullSCM"/>
      <canRoam>true</canRoam>
      <disabled>false</disabled>
      <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
      <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
      <triggers class="vector"/>
      <concurrentBuild>false</concurrentBuild>
      <builders/>
      <publishers/>
      <buildWrappers/>
    </project>
    """

    jobname = "foo_job"
    new_job = J.create_job(jobname, EMPTY_JOB_CONFIG)
    new_conf = new_job.get_config()

    # Create in a folder (Folders plugin)
    folder_job = J.create_job("folder1/folder2/job-name", EMPTY_JOB_CONFIG)

    root = et.fromstring(new_conf.strip())

    builders = root.find("builders")
    shell = et.SubElement(builders, "hudson.tasks.Shell")
    command = et.SubElement(shell, "command")
    command.text = "ls"

    print(et.tostring(root))
    J[jobname].update_config(et.tostring(root))

Create and delete jobs from XML file
------------------------------------

.. code-block:: python

    from pkg_resources import resource_string
    from jenkinsapi.jenkins import Jenkins

    jenkins = Jenkins("http://localhost:8080")
    job_name = "foo_job2"
    xml = resource_string("examples", "addjob.xml")

    print(xml)

    job = jenkins.create_job(jobname=job_name, xml=xml)

    # Get job from Jenkins by job name
    my_job = jenkins[job_name]
    print(my_job)

    # also can use
    # del jenkins[job_name]
    jenkins.delete_job(job_name)

Logging
-------

.. code-block:: python

    from jenkinsapi.utils.logging import configure_logging

    configure_logging("DEBUG")

Start parameterized build
-------------------------

.. code-block:: python

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

Create credentials
------------------

.. code-block:: python

    import logging
    from jenkinsapi.jenkins import Jenkins
    from jenkinsapi.credential import UsernamePasswordCredential, SSHKeyCredential

    log_level = getattr(logging, "DEBUG")
    logging.basicConfig(level=log_level)
    logger = logging.getLogger()

    jenkins_url = "http://localhost:8080/"

    jenkins = Jenkins(jenkins_url)

    # Get a list of all global credentials
    creds = jenkins.credentials
    logging.info(jenkins.credentials.keys())

    # Create username and password credential
    creds_description1 = "My_username_credential"
    cred_dict = {
        "description": creds_description1,
        "userName": "userName",
        "password": "password",
    }
    creds[creds_description1] = UsernamePasswordCredential(cred_dict)

    # Create ssh key credential that uses private key as a value
    # In jenkins credential dialog you need to paste credential
    # In your code it is advised to read it from file
    # For simplicity of this example reading key from file is not shown here
    def get_private_key_from_file():
        return "-----BEGIN RSA PRIVATE KEY-----"

    my_private_key = get_private_key_from_file()

    creds_description2 = "My_ssh_cred1"
    cred_dict = {
        "description": creds_description2,
        "userName": "userName",
        "passphrase": "",
        "private_key": my_private_key,
    }
    creds[creds_description2] = SSHKeyCredential(cred_dict)

    # Create ssh key credential that uses private key from path on Jenkins server
    my_private_key = "/home/jenkins/.ssh/special_key"

    creds_description3 = "My_ssh_cred2"
    cred_dict = {
        "description": creds_description3,
        "userName": "userName",
        "passphrase": "",
        "private_key": my_private_key,
    }
    creds[creds_description3] = SSHKeyCredential(cred_dict)

    # Remove credentials
    # We use credential description to find specific credential. This is the only
    # way to get specific credential from Jenkins via REST API
    del creds[creds_description1]
    del creds[creds_description2]
    del creds[creds_description3]

    # Remove all credentials
    for cred_descr in creds.keys():
        del creds[cred_descr]

Create slaves/nodes
-------------------

.. code-block:: python

    import logging
    import requests
    from jenkinsapi.jenkins import Jenkins
    from jenkinsapi.utils.requester import Requester

    requests.packages.urllib3.disable_warnings()

    log_level = getattr(logging, "DEBUG")
    logging.basicConfig(level=log_level)
    logger = logging.getLogger()

    jenkins_url = "http://localhost:8080/"
    username = "default_user"  # In case Jenkins requires authentication
    password = "default_password"

    jenkins = Jenkins(
        jenkins_url,
        requester=Requester(
            username, password, baseurl=jenkins_url, ssl_verify=False
        ),
    )

    # Create JNLP(Java Webstart) slave
    node_dict = {
        "num_executors": 1,  # Number of executors
        "node_description": "Test JNLP Node",  # Just a user friendly text
        "remote_fs": "/tmp",  # Remote workspace location
        "labels": "my_new_node",  # Space separated labels string
        "exclusive": True,  # Only run jobs assigned to it
    }
    new_jnlp_node = jenkins.nodes.create_node("My new webstart node", node_dict)

    node_dict = {
        "num_executors": 1,
        "node_description": "Test SSH Node",
        "remote_fs": "/tmp",
        "labels": "new_node",
        "exclusive": True,
        "host": "localhost",  # Remote hostname
        "port": 22,  # Remote post, usually 22
        "credential_description": "localhost cred",  # Credential to use
        # [Mandatory for SSH node!]
        # (see Credentials example)
        "jvm_options": "-Xmx2000M",  # JVM parameters
        "java_path": "/bin/java",  # Path to java
        "prefix_start_slave_cmd": "",
        "suffix_start_slave_cmd": "",
        "max_num_retries": 0,
        "retry_wait_time": 0,
        "retention": "OnDemand",  # Change to 'Always' for
        # immediate slave launch
        "ondemand_delay": 1,
        "ondemand_idle_delay": 5,
        "env": [  # Environment variables
            {"key": "TEST", "value": "VALUE"},
            {"key": "TEST2", "value": "value2"},
        ],
    }
    new_ssh_node = jenkins.nodes.create_node("My new SSH node", node_dict)

    # Take this slave offline
    if new_ssh_node.is_online():
        new_ssh_node.toggle_temporarily_offline()

        # Take this slave back online
        new_ssh_node.toggle_temporarily_offline()

    # Get a list of all slave names
    slave_names = jenkins.nodes.keys()

    # Get Node object
    my_node = jenkins.nodes["My new SSH node"]
    # Take this slave offline
    my_node.set_offline()

    # Delete slaves
    del jenkins.nodes["My new webstart node"]
    del jenkins.nodes["My new SSH node"]

Create views
------------

.. code-block:: python

    import logging
    from pkg_resources import resource_string
    from jenkinsapi.jenkins import Jenkins

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    jenkins_url = "http://localhost:8080/"

    jenkins = Jenkins(jenkins_url, lazy=True)

    # Create ListView in main view
    logger.info("Attempting to create new view")
    test_view_name = "SimpleListView"

    # Views object appears as a dictionary of views
    if test_view_name not in jenkins.views:
        new_view = jenkins.views.create(test_view_name)
        if new_view is None:
            logger.error("View %s was not created", test_view_name)
        else:
            logger.info(
                "View %s has been created: %s", new_view.name, new_view.baseurl
            )
    else:
        logger.info("View %s already exists", test_view_name)

    # No error is raised if view already exists
    logger.info("Attempting to create view that already exists")
    my_view = jenkins.views.create(test_view_name)

    logger.info("Create job and assign it to a view")
    job_name = "foo_job2"
    xml = resource_string("examples", "addjob.xml")

    my_job = jenkins.create_job(jobname=job_name, xml=xml)

    # add_job supports two parameters: job_name and job object
    # passing job object will remove verification calls to Jenkins
    my_view.add_job(job_name, my_job)
    assert len(my_view) == 1

    logger.info("Attempting to delete view that already exists")
    del jenkins.views[test_view_name]

    if test_view_name in jenkins.views:
        logger.error("View was not deleted")
    else:
        logger.info("View has been deleted")

    # No error will be raised when attempting to remove non-existing view
    logger.info("Attempting to delete view that does not exist")
    del jenkins.views[test_view_name]

    # Create CategorizedJobsView
    config = """
    <org.jenkinsci.plugins.categorizedview.CategorizedJobsView>
      <categorizationCriteria>
        <org.jenkinsci.plugins.categorizedview.GroupingRule>
          <groupRegex>.dev.</groupRegex>
          <namingRule>Development</namingRule>
        </org.jenkinsci.plugins.categorizedview.GroupingRule>
        <org.jenkinsci.plugins.categorizedview.GroupingRule>
          <groupRegex>.hml.</groupRegex>
          <namingRule>Homologation</namingRule>
        </org.jenkinsci.plugins.categorizedview.GroupingRule>
      </categorizationCriteria>
    </org.jenkinsci.plugins.categorizedview.CategorizedJobsView>
    """
    view = jenkins.views.create(
        "My categorized jobs view", jenkins.views.CATEGORIZED_VIEW, config=config
    )

Delete all the nodes except master
----------------------------------

.. code-block:: python

    import logging
    from jenkinsapi.jenkins import Jenkins

    logging.basicConfig()

    j = Jenkins("http://localhost:8080")

    for node_id, _ in j.get_nodes().iteritems():
        if node_id != "master":
            print(node_id)
            j.delete_node(node_id)

    # Alternative way - this method will not delete 'master'
    for node in j.nodes.keys():
        del j.nodes[node]

Use JenkinsAPI to fetch the config XML of a job.
------------------------------------------------

.. code-block:: python

    from jenkinsapi.jenkins import Jenkins

    jenkins = Jenkins("http://localhost:8080")
    jobName = jenkins.keys()[0]  # get the first job

    config = jenkins[jobName].get_config()

    print(config)

Print currently installed plugin information
--------------------------------------------

.. code-block:: python

    from jenkinsapi.jenkins import Jenkins

    plugin_name = "subversion"
    jenkins = Jenkins("http://localhost:8080")
    plugin = jenkins.get_plugins()[plugin_name]

    print(repr(plugin))

Print version info from last good build
---------------------------------------

.. code-block:: python

    from jenkinsapi.jenkins import Jenkins

    job_name = "foo"
    jenkins = Jenkins("http://localhost:8080")
    job = jenkins[job_name]
    lgb = job.get_last_good_build()
    print(lgb.get_revision())

Search artifacts by name
------------------------

.. code-block:: python

    from jenkinsapi.api import search_artifacts

    jenkinsurl = "http://localhost:8080"
    jobid = "foo"
    # I need a build that contains all of these
    artifact_ids = ["test1.txt", "test2.txt"]
    result = search_artifacts(jenkinsurl, jobid, artifact_ids)
    print((repr(result)))

Search artifacts by regexp
--------------------------

.. code-block:: python

    import re
    from jenkinsapi.api import search_artifact_by_regexp

    jenkinsurl = "http://localhost:8080"
    jobid = "foo"
    artifact_regexp = re.compile(r"test1\.txt")  # A file name I want.
    result = search_artifact_by_regexp(jenkinsurl, jobid, artifact_regexp)
    print((repr(result)))

Use NestedViews Jenkins plugin
------------------------------

.. code-block:: python

    """
    This example requires NestedViews plugin to be installed in Jenkins
    You need to have at least one job in your Jenkins to see views
    """

    import logging
    from pkg_resources import resource_string
    from jenkinsapi.views import Views
    from jenkinsapi.jenkins import Jenkins

    log_level = getattr(logging, "DEBUG")
    logging.basicConfig(level=log_level)
    logger = logging.getLogger()

    jenkins_url = "http://127.0.0.1:8080/"
    jenkins = Jenkins(jenkins_url)

    job_name = "foo_job2"
    xml = resource_string("examples", "addjob.xml")
    j = jenkins.create_job(jobname=job_name, xml=xml)

    # Create ListView in main view
    logger.info("Attempting to create new nested view")
    top_view = jenkins.views.create("TopView", Views.NESTED_VIEW)
    logger.info("top_view is %s", top_view)
    if top_view is None:
        logger.error("View was not created")
    else:
        logger.info("View has been created")

    print("top_view.views=", top_view.views.keys())
    logger.info("Attempting to create view inside nested view")
    sub_view = top_view.views.create("SubView")
    if sub_view is None:
        logger.info("View was not created")
    else:
        logger.error("View has been created")

    logger.info("Attempting to delete sub_view")
    del top_view.views["SubView"]
    if "SubView" in top_view.views:
        logger.error("SubView was not deleted")
    else:
        logger.info("SubView has been deleted")

    # Another way of creating sub view
    # This way sub view will have jobs in it
    logger.info("Attempting to create view with jobs inside nested view")
    top_view.views["SubView"] = job_name
    if "SubView" not in top_view.views:
        logger.error("View was not created")
    else:
        logger.info("View has been created")

    logger.info("Attempting to delete sub_view")
    del top_view.views["SubView"]
    if "SubView" in top_view.views:
        logger.error("SubView was not deleted")
    else:
        logger.info("SubView has been deleted")

    logger.info("Attempting to delete top view")
    del jenkins.views["TopView"]
    if "TopView" not in jenkins.views:
        logger.info("View has been deleted")
    else:
        logger.error("View was not deleted")

    # Delete job that we created
    jenkins.delete_job(job_name)

Use Crumbs
----------

.. code-block:: python

    from jenkinsapi.jenkins import Jenkins

    jenkins = Jenkins(
        "http://localhost:8080",
        username="admin",
        password="password",
        use_crumb=True,
    )

    for job_name in jenkins.jobs:
        print(job_name)

Note: Results may be incomplete. `View all files on GitHub. <https://github.com/pycontribs/jenkinsapi/tree/master/examples/how_to>`_
