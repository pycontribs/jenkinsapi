"""
How to create slaves/nodes
"""

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
