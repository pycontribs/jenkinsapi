"""
This example shows how to create credentials
"""

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
# In your code it is adviced to read it from file
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
