"""
Module for jenkinsapi Node class
"""

from __future__ import annotations

import json
import logging

import xml.etree.ElementTree as ET

import time
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.custom_exceptions import PostRequired, TimeOut
from jenkinsapi.custom_exceptions import JenkinsAPIException
from urllib.parse import quote as urlquote

log = logging.getLogger(__name__)


class Node(JenkinsBase):
    """
    Class to hold information on nodes that are attached as slaves
    to the master jenkins instance
    """

    def __init__(
        self,
        jenkins_obj: "Jenkins",
        baseurl: str,
        nodename: str,
        node_dict,
        poll: bool = True,
    ) -> None:
        """
        Init a node object by providing all relevant pointers to it
        :param jenkins_obj: ref to the jenkins obj
        :param baseurl: basic url for querying information on a node
            If url is not set - object will construct it itself. This is
            useful when node is being created and not exists in Jenkins yet
        :param nodename: hostname of the node
        :param dict node_dict: Dict with node parameters as described below
        :param bool poll: set to False if node does not exist or automatic
            refresh from Jenkins is not required. Default is True.
            If baseurl parameter is set to None - poll parameter will be
            set to False

        JNLP Node:
            {
                'num_executors': int,
                'node_description': str,
                'remote_fs': str,
                'labels': str,
                'exclusive': bool
            }

        SSH Node:
        {
            'num_executors': int,
            'node_description': str,
            'remote_fs': str,
            'labels': str,
            'exclusive': bool,
            'host': str,
            'port': int
            'credential_description': str,
            'jvm_options': str,
            'java_path': str,
            'prefix_start_slave_cmd': str,
            'suffix_start_slave_cmd': str
            'max_num_retries': int,
            'retry_wait_time': int,
            'retention': str ('Always' or 'OnDemand')
            'ondemand_delay': int (only for OnDemand retention)
            'ondemand_idle_delay': int (only for OnDemand retention)
            'env': [
                {
                    'key':'TEST',
                    'value':'VALUE'
                },
                {
                    'key':'TEST2',
                    'value':'value2'
                }
            ],
            'tool_location': [
                {
                    "key": "hudson.tasks.Maven$MavenInstallation$DescriptorImpl@Maven 3.0.5",  # noqa
                    "home": "/home/apache-maven-3.0.5/"
                },
                {
                    "key": "hudson.plugins.git.GitTool$DescriptorImpl@Default",
                    "home": "/home/git-3.0.5/"
                },
            ]
        }

        :return: None
        :return: Node obj
        """
        self.name: str = nodename
        self.jenkins: "Jenkins" = jenkins_obj
        if not baseurl:
            poll = False
            baseurl = f"{self.jenkins.baseurl}/computer/{self.name}"
        JenkinsBase.__init__(self, baseurl, poll=poll)
        self.node_attributes: dict = node_dict
        self._element_tree = None
        self._config = None

    def get_node_attributes(self) -> dict:
        """
        Gets node attributes as dict

        Used by Nodes object when node is created

        :return: Node attributes dict formatted for Jenkins API request
            to create node
        """
        na: dict = self.node_attributes
        if not na.get("credential_description", False):
            # If credentials description is not present - we will create
            # JNLP node
            launcher = {"stapler-class": "hudson.slaves.JNLPLauncher"}
        else:
            try:
                credential = self.jenkins.credentials[
                    na["credential_description"]
                ]
            except KeyError:
                raise JenkinsAPIException(
                    'Credential with description "%s"'
                    " not found" % na["credential_description"]
                )

            retries: int = (
                na["max_num_retries"] if "max_num_retries" in na else 0
            )
            re_wait: int = (
                na["retry_wait_time"] if "retry_wait_time" in na else 0
            )
            launcher = {
                "stapler-class": "hudson.plugins.sshslaves.SSHLauncher",
                "$class": "hudson.plugins.sshslaves.SSHLauncher",
                "host": na["host"],
                "port": na["port"],
                "credentialsId": credential.credential_id,
                "jvmOptions": na["jvm_options"],
                "javaPath": na["java_path"],
                "prefixStartSlaveCmd": na["prefix_start_slave_cmd"],
                "suffixStartSlaveCmd": na["suffix_start_slave_cmd"],
                "maxNumRetries": retries,
                "retryWaitTime": re_wait,
            }

        retention = {
            "stapler-class": "hudson.slaves.RetentionStrategy$Always",
            "$class": "hudson.slaves.RetentionStrategy$Always",
        }
        if "retention" in na and na["retention"].lower() == "ondemand":
            retention = {
                "stapler-class": "hudson.slaves.RetentionStrategy$Demand",
                "$class": "hudson.slaves.RetentionStrategy$Demand",
                "inDemandDelay": na["ondemand_delay"],
                "idleDelay": na["ondemand_idle_delay"],
            }

        node_props: dict = {"stapler-class-bag": "true"}
        if "env" in na:
            node_props.update(
                {
                    "hudson-slaves-EnvironmentVariablesNodeProperty": {
                        "env": na["env"]
                    }
                }
            )
        if "tool_location" in na:
            node_props.update(
                {
                    "hudson-tools-ToolLocationNodeProperty": {
                        "locations": na["tool_location"]
                    }
                }
            )

        params = {
            "name": self.name,
            "type": "hudson.slaves.DumbSlave$DescriptorImpl",
            "json": json.dumps(
                {
                    "name": self.name,
                    "nodeDescription": na.get("node_description", ""),
                    "numExecutors": na["num_executors"],
                    "remoteFS": na["remote_fs"],
                    "labelString": na["labels"],
                    "mode": "EXCLUSIVE" if na["exclusive"] else "NORMAL",
                    "retentionStrategy": retention,
                    "type": "hudson.slaves.DumbSlave",
                    "nodeProperties": node_props,
                    "launcher": launcher,
                }
            ),
        }

        return params

    def get_jenkins_obj(self) -> "Jenkins":
        return self.jenkins

    def __str__(self) -> str:
        return self.name

    def is_online(self) -> bool:
        return not self.poll(tree="offline")["offline"]

    def is_temporarily_offline(self) -> bool:
        return self.poll(tree="temporarilyOffline")["temporarilyOffline"]

    def is_jnlpagent(self) -> bool:
        return self._data["jnlpAgent"]

    def is_idle(self) -> bool:
        return self.poll(tree="idle")["idle"]

    def set_online(self) -> None:
        """
        Set node online.
        Before change state verify client state: if node set 'offline'
        but 'temporarilyOffline' is not set - client has connection problems
        and AssertionError raised.
        If after run node state has not been changed raise AssertionError.
        """
        self.poll()
        # Before change state check if client is connected
        if self._data["offline"] and not self._data["temporarilyOffline"]:
            raise AssertionError(
                "Node is offline and not marked as "
                "temporarilyOffline, check client "
                "connection: offline = %s, "
                "temporarilyOffline = %s"
                % (self._data["offline"], self._data["temporarilyOffline"])
            )

        if self._data["offline"] and self._data["temporarilyOffline"]:
            self.toggle_temporarily_offline()
            if self._data["offline"]:
                raise AssertionError(
                    "The node state is still offline, "
                    "check client connection:"
                    " offline = %s, "
                    "temporarilyOffline = %s"
                    % (self._data["offline"], self._data["temporarilyOffline"])
                )

    def set_offline(self, message="requested from jenkinsapi") -> None:
        """
        Set node offline.
        If after run node state has not been changed raise AssertionError.
        : param message: optional string explain why you are taking this
            node offline
        """
        if not self._data["offline"]:
            self.toggle_temporarily_offline(message)
            data = self.poll(tree="offline,temporarilyOffline")
            if not data["offline"]:
                raise AssertionError(
                    "The node state is still online:"
                    + "offline = %s , temporarilyOffline = %s"
                    % (data["offline"], data["temporarilyOffline"])
                )

    def launch(self) -> None:
        """
        Tries to launch a connection with the slave if it is currently
        disconnected. Because launching a connection with the slave does not
        mean it is online (a slave can be launched, but set offline), this
        function does not check if the launch was successful.
        """
        if not self._data["launchSupported"]:
            raise AssertionError("The node does not support manually launch.")

        if not self._data["manualLaunchAllowed"]:
            raise AssertionError(
                "It is not allowed to manually launch this node."
            )

        url = self.baseurl + "/launchSlaveAgent"
        html_result = self.jenkins.requester.post_and_confirm_status(
            url, data={}
        )
        log.debug(html_result)

    def toggle_temporarily_offline(
        self, message="requested from jenkinsapi"
    ) -> None:
        """
        Switches state of connected node (online/offline) and
        set 'temporarilyOffline' property (True/False)
        Calling the same method again will bring node status back.
        :param message: optional string can be used to explain why you
            are taking this node offline
        """
        initial_state = self.is_temporarily_offline()
        url = (
            self.baseurl + "/toggleOffline?offlineMessage=" + urlquote(message)
        )
        try:
            html_result = self.jenkins.requester.get_and_confirm_status(url)
        except PostRequired:
            html_result = self.jenkins.requester.post_and_confirm_status(
                url, data={}
            )

        self.poll()
        log.debug(html_result)
        state = self.is_temporarily_offline()
        if initial_state == state:
            raise AssertionError(
                "The node state has not changed: temporarilyOffline = %s"
                % state
            )

    def update_offline_reason(self, reason: str) -> None:
        """
        Update offline reason on a temporary offline clsuter
        """

        if self.is_temporarily_offline():
            url = (
                self.baseurl
                + "/changeOfflineCause?offlineMessage="
                + urlquote(reason)
            )
            self.jenkins.requester.post_and_confirm_status(url, data={})

    def offline_reason(self) -> str:
        return self._data["offlineCauseReason"]

    @property
    def _et(self):
        return self._get_config_element_tree()

    def _get_config_element_tree(self) -> ET.Element:
        """
        Returns an xml element tree for the node's config.xml. The
        resulting tree is cached for quick lookup.
        """
        if self._config is None:
            self.load_config()

        if self._element_tree is None:
            self._element_tree = ET.fromstring(self._config)
        return self._element_tree

    def get_config(self) -> str:
        """
        Returns the config.xml from the node.
        """
        response = self.jenkins.requester.get_and_confirm_status(
            "%(baseurl)s/config.xml" % self.__dict__
        )
        return response.text

    def load_config(self) -> None:
        """
        Loads the config.xml for the node allowing it to be re-queried
        without generating new requests.
        """
        if self.name == "Built-In Node":
            raise JenkinsAPIException("Built-In node does not have config.xml")

        self._config = self.get_config()
        self._get_config_element_tree()

    def upload_config(self, config_xml: str) -> None:
        """
        Uploads config_xml to the config.xml for the node.
        """
        if self.name == "Built-In Node":
            raise JenkinsAPIException("Built-In node does not have config.xml")

        self.jenkins.requester.post_and_confirm_status(
            "%(baseurl)s/config.xml" % self.__dict__, data=config_xml
        )

    def get_labels(self) -> str | None:
        """
        Returns the labels for a slave as a string with each label
        separated by the ' ' character.
        """
        return self.get_config_element("label")

    def get_num_executors(self) -> str:
        try:
            return self.get_config_element("numExecutors")
        except JenkinsAPIException:
            return self._data["numExecutors"]

    def set_num_executors(self, value: int | str) -> None:
        """
        Sets number of executors for node

        Warning! Setting number of executors on master node will erase all
        other settings
        """
        set_value = value if isinstance(value, str) else str(value)

        if self.name == "Built-In Node":
            # master node doesn't have config.xml, so we're going to submit
            # form here
            data = "json=%s" % urlquote(
                json.dumps(
                    {
                        "numExecutors": set_value,
                        "nodeProperties": {"stapler-class-bag": "true"},
                    }
                )
            )

            url = self.baseurl + "/configSubmit"
            self.jenkins.requester.post_and_confirm_status(url, data=data)
        else:
            self.set_config_element("numExecutors", set_value)

        self.poll()

    def get_config_element(self, el_name: str) -> str:
        """
        Returns simple config element.

        Better not to be used to return "nodeProperties" or "launcher"
        """
        return self._et.find(el_name).text

    def set_config_element(self, el_name: str, value: str) -> None:
        """
        Sets simple config element
        """
        self._et.find(el_name).text = value
        xml_str = ET.tostring(self._et)
        self.upload_config(xml_str)

    def get_monitor(self, monitor_name: str, poll_monitor=True) -> str:
        """
        Polls the node returning one of the monitors in the monitorData
        branch of the returned node api tree.
        """
        monitor_data_key = "monitorData"
        if poll_monitor:
            # polling as monitors like response time can be updated
            monitor_data = self.poll(tree=monitor_data_key)[monitor_data_key]
        else:
            monitor_data = self._data[monitor_data_key]

        full_monitor_name = "hudson.node_monitors.{0}".format(monitor_name)
        if full_monitor_name not in monitor_data:
            raise AssertionError("Node monitor %s not found" % monitor_name)

        return monitor_data[full_monitor_name]

    def get_available_physical_memory(self) -> int:
        """
        Returns the node's available physical memory in bytes.
        """
        monitor_data = self.get_monitor("SwapSpaceMonitor")
        return monitor_data["availablePhysicalMemory"]

    def get_available_swap_space(self) -> int:
        """
        Returns the node's available swap space in bytes.
        """
        monitor_data = self.get_monitor("SwapSpaceMonitor")
        return monitor_data["availableSwapSpace"]

    def get_total_physical_memory(self) -> int:
        """
        Returns the node's total physical memory in bytes.
        """
        monitor_data = self.get_monitor("SwapSpaceMonitor")
        return monitor_data["totalPhysicalMemory"]

    def get_total_swap_space(self) -> int:
        """
        Returns the node's total swap space in bytes.
        """
        monitor_data = self.get_monitor("SwapSpaceMonitor")
        return monitor_data["totalSwapSpace"]

    def get_workspace_path(self) -> str:
        """
        Returns the local path to the node's Jenkins workspace directory.
        """
        monitor_data = self.get_monitor("DiskSpaceMonitor")
        return monitor_data["path"]

    def get_workspace_size(self) -> int:
        """
        Returns the size in bytes of the node's Jenkins workspace directory.
        """
        monitor_data = self.get_monitor("DiskSpaceMonitor")
        return monitor_data["size"]

    def get_temp_path(self) -> str:
        """
        Returns the local path to the node's temp directory.
        """
        monitor_data = self.get_monitor("TemporarySpaceMonitor")
        return monitor_data["path"]

    def get_temp_size(self) -> int:
        """
        Returns the size in bytes of the node's temp directory.
        """
        monitor_data = self.get_monitor("TemporarySpaceMonitor")
        return monitor_data["size"]

    def get_architecture(self) -> str:
        """
        Returns the system architecture of the node eg. "Linux (amd64)".
        """
        # no need to poll as the architecture will never change
        return self.get_monitor("ArchitectureMonitor", poll_monitor=False)

    def block_until_idle(self, timeout: int, poll_time: int = 5) -> None:
        """
        Blocks until the node become idle.
        :param timeout: Time in second when the wait is aborted.
        :param poll_time: Interval in seconds between each check.
        :@raise TimeOut
        """
        start_time = time.time()
        while not self.is_idle() and (time.time() - start_time) < timeout:
            log.debug(
                "Waiting for the node to become idle. Elapsed time: %s",
                (time.time() - start_time),
            )
            time.sleep(poll_time)

        if not self.is_idle():
            raise TimeOut(
                "The node has not become idle after {} minutes.".format(
                    timeout / 60
                )
            )

    def get_response_time(self) -> int:
        """
        Returns the node's average response time.
        """
        monitor_data = self.get_monitor("ResponseTimeMonitor")
        return monitor_data["average"]

    def get_clock_difference(self) -> int:
        """
        Returns the difference between the node's clock and
        the master Jenkins clock.
        Used to detect out of sync clocks.
        """
        monitor_data = self.get_monitor("ClockMonitor")
        return monitor_data["diff"]
