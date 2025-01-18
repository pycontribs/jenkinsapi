"""
Module for jenkinsapi Credential class
"""

import logging
import xml.etree.cElementTree as ET

log = logging.getLogger(__name__)


class Credential(object):
    """
    Base abstract class for credentials

    Credentials returned from Jenkins don't hold any sensitive information,
    so there is nothing useful can be done with existing credentials
    besides attaching them to Nodes or other objects.

    You can create concrete Credential instance: UsernamePasswordCredential or
    SSHKeyCredential by passing credential's description and credential dict.

    Each class expects specific credential dict, see below.
    """

    # pylint: disable=unused-argument

    def __init__(self, cred_dict, jenkins_class=""):
        """
        Create credential

        :param str description: as Jenkins doesn't allow human friendly names
            for credentials and makes "displayName" itself,
            there is no way to find credential later,
            this field is used to distinguish between credentials
        :param dict cred_dict: dict containing credential information
        """
        self.credential_id = cred_dict.get("credential_id", "")
        self.description = cred_dict["description"]
        self.fullname = cred_dict.get("fullName", "")
        self.displayname = cred_dict.get("displayName", "")
        self.jenkins_class = jenkins_class

    def __str__(self):
        return self.description

    def get_attributes(self):
        pass

    def get_attributes_xml(self):
        pass

    def _get_attributes_xml(self, data):
        root = ET.Element(self.jenkins_class)
        for key in data:
            value = data[key]
            if isinstance(value, dict):
                node = ET.SubElement(root, key)
                if "stapler-class" in value:
                    node.attrib["class"] = value["stapler-class"]
                for sub_key in value:
                    ET.SubElement(node, sub_key).text = value[sub_key]
            else:
                ET.SubElement(root, key).text = data[key]
        return ET.tostring(root)


class UsernamePasswordCredential(Credential):
    """
    Username and password credential

    Constructor expects following dict:
        {
            'credential_id': str,   Automatically set by jenkinsapi
            'displayName': str,     Automatically set by Jenkins
            'fullName': str,        Automatically set by Jenkins
            'typeName': str,        Automatically set by Jenkins
            'description': str,
            'userName': str,
            'password': str
        }

    When creating credential via jenkinsapi automatic fields not need to be in
    dict
    """

    def __init__(self, cred_dict: dict) -> None:
        jenkins_class: str = (
            "com.cloudbees.plugins.credentials.impl."
            "UsernamePasswordCredentialsImpl"
        )
        super(UsernamePasswordCredential, self).__init__(
            cred_dict, jenkins_class
        )
        if "typeName" in cred_dict:
            username: str = cred_dict["displayName"].split("/")[0]
        else:
            username: str = cred_dict["userName"]

        self.username: str = username
        self.password: str = cred_dict.get("password", "")

    def get_attributes(self):
        """
        Used by Credentials object to create credential in Jenkins
        """
        c_id = "" if self.credential_id is None else self.credential_id
        return {
            "stapler-class": self.jenkins_class,
            "Submit": "OK",
            "json": {
                "": "1",
                "credentials": {
                    "stapler-class": self.jenkins_class,
                    "id": c_id,
                    "username": self.username,
                    "password": self.password,
                    "description": self.description,
                },
            },
        }

    def get_attributes_xml(self):
        """
        Used by Credentials object to update a credential in Jenkins
        """
        c_id = "" if self.credential_id is None else self.credential_id
        data = {
            "id": c_id,
            "username": self.username,
            "password": self.password,
            "description": self.description,
        }
        return super(UsernamePasswordCredential, self)._get_attributes_xml(
            data
        )


class SecretTextCredential(Credential):
    """
    Secret text credential

    Constructor expects following dict:
        {
            'credential_id': str,   Automatically set by jenkinsapi
            'displayName': str,     Automatically set by Jenkins
            'fullName': str,        Automatically set by Jenkins
            'typeName': str,        Automatically set by Jenkins
            'description': str,
            'secret': str,
        }

    When creating credential via jenkinsapi automatic fields not need to be in
    dict
    """

    def __init__(self, cred_dict):
        jenkins_class = (
            "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"
        )
        super(SecretTextCredential, self).__init__(cred_dict, jenkins_class)
        self.secret = cred_dict.get("secret", None)

    def get_attributes(self):
        """
        Used by Credentials object to create credential in Jenkins
        """
        c_id = "" if self.credential_id is None else self.credential_id
        return {
            "stapler-class": self.jenkins_class,
            "Submit": "OK",
            "json": {
                "": "1",
                "credentials": {
                    "stapler-class": self.jenkins_class,
                    "$class": self.jenkins_class,
                    "id": c_id,
                    "secret": self.secret,
                    "description": self.description,
                },
            },
        }

    def get_attributes_xml(self):
        """
        Used by Credentials object to update a credential in Jenkins
        """
        c_id = "" if self.credential_id is None else self.credential_id
        data = {
            "id": c_id,
            "secret": self.secret,
            "description": self.description,
        }
        return super(SecretTextCredential, self)._get_attributes_xml(data)


class SSHKeyCredential(Credential):
    """
    SSH key credential

    Constructr expects following dict:
        {
            'credential_id': str,   Automatically set by jenkinsapi
            'displayName': str,     Automatically set by Jenkins
            'fullName': str,        Automatically set by Jenkins
            'typeName': str,        Automatically set by Jenkins
            'description': str,
            'userName': str,
            'passphrase': str,      SSH key passphrase,
            'private_key': str      Private SSH key
        }

    private_key value is parsed to find type of credential to create:

    private_key starts with -       the value is private key itself

    These credential variations are no longer supported by SSH Credentials
    plugin. jenkinsapi will raise ValueError if they are used:

    private_key starts with /       the value is a path to key
    private_key starts with ~       the value is a key from ~/.ssh

    When creating credential via jenkinsapi automatic fields not need to be in
    dict
    """

    def __init__(self, cred_dict: dict) -> None:
        jenkins_class: str = (
            "com.cloudbees.jenkins.plugins.sshcredentials.impl."
            "BasicSSHUserPrivateKey"
        )
        super(SSHKeyCredential, self).__init__(cred_dict, jenkins_class)
        if "typeName" in cred_dict:
            username: str = cred_dict["displayName"].split(" ")[0]
        else:
            username: str = cred_dict["userName"]

        self.username: str = username
        self.passphrase: str = cred_dict.get("passphrase", "")

        if "private_key" not in cred_dict or cred_dict["private_key"] is None:
            self.key_type: int = -1
            self.key_value: str = ""
        elif cred_dict["private_key"].startswith("-"):
            self.key_type: int = 0
            self.key_value: str = cred_dict["private_key"]
        else:
            raise ValueError("Invalid private_key value")

    @property
    def attrs(self):
        if self.key_type == 0:
            c_class = self.jenkins_class + "$DirectEntryPrivateKeySource"
        elif self.key_type == 1:
            c_class = self.jenkins_class + "$FileOnMasterPrivateKeySource"
        elif self.key_type == 2:
            c_class = self.jenkins_class + "$UsersPrivateKeySource"
        else:
            c_class = None

        attrs = {
            "value": self.key_type,
            "privateKey": self.key_value,
            "stapler-class": c_class,
        }
        # We need one more attr when using the key file on master.
        if self.key_type == 1:
            attrs["privateKeyFile"] = self.key_value

        return attrs

    def get_attributes(self):
        """
        Used by Credentials object to create credential in Jenkins
        """

        c_id = "" if self.credential_id is None else self.credential_id

        return {
            "stapler-class": self.attrs["stapler-class"],
            "Submit": "OK",
            "json": {
                "": "1",
                "credentials": {
                    "scope": "GLOBAL",
                    "id": c_id,
                    "username": self.username,
                    "description": self.description,
                    "privateKeySource": self.attrs,
                    "passphrase": self.passphrase,
                    "stapler-class": self.jenkins_class,
                    "$class": self.jenkins_class,
                },
            },
        }

    def get_attributes_xml(self):
        """
        Used by Credentials object to update a credential in Jenkins
        """
        c_id = "" if self.credential_id is None else self.credential_id
        data = {
            "id": c_id,
            "username": self.username,
            "description": self.description,
            "privateKeySource": self.attrs,
            "passphrase": self.passphrase,
        }
        return super(SSHKeyCredential, self)._get_attributes_xml(data)


class AmazonWebServicesCredentials(Credential):
    """
    AWS credential using the CloudBees AWS Credentials Plugin
    See
    https://wiki.jenkins.io/display/JENKINS/CloudBees+AWS+Credentials+Plugin

    Constructor expects following dict:
        {
            'credential_id': str,   Automatically set by jenkinsapi
            'displayName': str,     Automatically set by Jenkins
            'fullName': str,        Automatically set by Jenkins
            'description': str,
            'accessKey': str,
            'secretKey': str,
            'iamRoleArn': str,
            'iamMfaSerialNumber': str
        }

    When creating credential via jenkinsapi automatic fields not need to be in
    dict
    """

    def __init__(self, cred_dict):
        jenkins_class = (
            "com.cloudbees.jenkins.plugins.awscredentials.AWSCredentialsImpl"
        )
        super(AmazonWebServicesCredentials, self).__init__(
            cred_dict, jenkins_class
        )

        self.access_key = cred_dict["accessKey"]
        self.secret_key = cred_dict["secretKey"]
        self.iam_role_arn = cred_dict.get("iamRoleArn", "")
        self.iam_mfa_serial_number = cred_dict.get("iamMfaSerialNumber", "")

    def get_attributes(self):
        """
        Used by Credentials object to create credential in Jenkins
        """
        c_id = "" if self.credential_id is None else self.credential_id
        return {
            "stapler-class": self.jenkins_class,
            "Submit": "OK",
            "json": {
                "": "1",
                "credentials": {
                    "stapler-class": self.jenkins_class,
                    "$class": self.jenkins_class,
                    "id": c_id,
                    "accessKey": self.access_key,
                    "secretKey": self.secret_key,
                    "iamRoleArn": self.iam_role_arn,
                    "iamMfaSerialNumber": self.iam_mfa_serial_number,
                    "description": self.description,
                },
            },
        }

    def get_attributes_xml(self):
        """
        Used by Credentials object to update a credential in Jenkins
        """
        c_id = "" if self.credential_id is None else self.credential_id
        data = {
            "id": c_id,
            "accessKey": self.access_key,
            "secretKey": self.secret_key,
            "iamRoleArn": self.iam_role_arn,
            "iamMfaSerialNumber": self.iam_mfa_serial_number,
            "description": self.description,
        }
        return super(AmazonWebServicesCredentials, self)._get_attributes_xml(
            data
        )
