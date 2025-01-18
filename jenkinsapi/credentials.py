"""
This module implements the Credentials class, which is intended to be a
container-like interface for all of the Global credentials defined on a single
Jenkins node.
"""

from __future__ import annotations

from typing import Iterator

import logging
from urllib.parse import urlencode

from jenkinsapi.credential import Credential
from jenkinsapi.credential import UsernamePasswordCredential
from jenkinsapi.credential import SecretTextCredential
from jenkinsapi.credential import SSHKeyCredential
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.custom_exceptions import JenkinsAPIException

log: logging.Logger = logging.getLogger(__name__)


class Credentials(JenkinsBase):
    """
    This class provides a container-like API which gives
    access to all global credentials on a Jenkins node.

    Returns a list of Credential Objects.
    """

    def __init__(self, baseurl: str, jenkins_obj: "Jenkins"):
        self.baseurl: str = baseurl
        self.jenkins: "Jenkins" = jenkins_obj
        JenkinsBase.__init__(self, baseurl)

        self.credentials = self._data["credentials"]

    def _poll(self, tree=None):
        url: str = self.python_api_url(self.baseurl) + "?depth=2"
        data = self.get_data(url, tree=tree)
        credentials = data["credentials"]
        for cred_id, cred_dict in credentials.items():
            cred_dict["credential_id"] = cred_id
            credentials[cred_id] = self._make_credential(cred_dict)

        return data

    def __str__(self) -> str:
        return "Global Credentials @ %s" % self.baseurl

    def get_jenkins_obj(self) -> "Jenkins":
        return self.jenkins

    def __iter__(self) -> Iterator[Credential]:
        for cred in self.credentials.values():
            yield cred.description

    def __contains__(self, description: str) -> bool:
        return description in self.keys()

    def iterkeys(self):
        return self.__iter__()

    def keys(self):
        return list(self.iterkeys())

    def iteritems(self) -> Iterator[str, "Credential"]:
        for cred in self.credentials.values():
            yield cred.description, cred

    def __getitem__(self, description: str) -> "Credential":
        for cred in self.credentials.values():
            if cred.description == description:
                return cred

        raise KeyError(
            'Credential with description "%s" not found' % description
        )

    def __len__(self) -> int:
        return len(self.keys())

    def __setitem__(self, description: str, credential: "Credential"):
        """
        Creates Credential in Jenkins using username, password and description
        Description must be unique in Jenkins instance
        because it is used to find Credential later.

        If description already exists - this method is going to update
        existing Credential

        :param str description: Credential description
        :param tuple credential_tuple: (username, password, description) tuple.
        """
        if description not in self:
            params = credential.get_attributes()
            url = "%s/createCredentials" % self.baseurl
            try:
                self.jenkins.requester.post_and_confirm_status(
                    url, params={}, data=urlencode(params)
                )
            except JenkinsAPIException as jae:
                raise JenkinsAPIException(
                    "Latest version of Credentials "
                    "plugin is required to be able "
                    "to create credentials. "
                    "Original exception: %s" % str(jae)
                )
        else:
            cred_id = self[description].credential_id
            credential.credential_id = cred_id
            params = credential.get_attributes_xml()
            url = "%s/credential/%s/config.xml" % (self.baseurl, cred_id)
            try:
                self.jenkins.requester.post_xml_and_confirm_status(
                    url, params={}, data=params
                )
            except JenkinsAPIException as jae:
                raise JenkinsAPIException(
                    "Latest version of Credentials "
                    "plugin is required to be able "
                    "to update credentials. "
                    "Original exception: %s" % str(jae)
                )

        self.poll()
        self.credentials = self._data["credentials"]
        if description not in self:
            raise JenkinsAPIException("Problem creating/updating credential.")

    def get(self, item, default):
        return self[item] if item in self else default

    def __delitem__(self, description: str):
        if description not in self:
            raise KeyError(
                'Credential with description "%s" not found' % description
            )
        params = {"Submit": "OK", "json": {}}
        url = "%s/credential/%s/doDelete" % (
            self.baseurl,
            self[description].credential_id,
        )
        try:
            self.jenkins.requester.post_and_confirm_status(
                url, params={}, data=urlencode(params)
            )
        except JenkinsAPIException as jae:
            raise JenkinsAPIException(
                "Latest version of Credentials "
                "required to be able to create "
                "credentials. Original exception: %s" % str(jae)
            )
        self.poll()
        self.credentials = self._data["credentials"]
        if description in self:
            raise JenkinsAPIException("Problem deleting credential.")

    def _make_credential(self, cred_dict):
        if cred_dict["typeName"] == "Username with password":
            cr = UsernamePasswordCredential(cred_dict)
        elif cred_dict["typeName"] == "SSH Username with private key":
            cr = SSHKeyCredential(cred_dict)
        elif cred_dict["typeName"] == "Secret text":
            cr = SecretTextCredential(cred_dict)
        else:
            cr = Credential(cred_dict)

        return cr


class Credentials2x(Credentials):
    """
    This class provides a container-like API which gives
    access to all global credentials on a Jenkins node.

    Returns a list of Credential Objects.
    """

    def _poll(self, tree=None):
        url = self.python_api_url(self.baseurl) + "?depth=2"
        data = self.get_data(url, tree=tree)
        credentials = data["credentials"]
        new_creds = {}
        for cred_dict in credentials:
            cred_dict["credential_id"] = cred_dict["id"]
            new_creds[cred_dict["id"]] = self._make_credential(cred_dict)

        data["credentials"] = new_creds

        return data


class CredentialsById(Credentials2x):
    """
    This class provides a container-like API which gives
    access to all global credentials on a Jenkins node.

    Returns a list of Credential Objects.
    """

    def __iter__(self):
        for cred in self.credentials.values():
            yield cred.credential_id

    def __contains__(self, credential_id):
        return credential_id in self.keys()

    def iteritems(self):
        for cred in self.credentials.values():
            yield cred.credential_id, cred

    def __getitem__(self, credential_id):
        for cred in self.credentials.values():
            if cred.credential_id == credential_id:
                return cred

        raise KeyError(
            'Credential with credential_id "%s" not found' % credential_id
        )
