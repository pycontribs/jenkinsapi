"""
Module for jenkinsapi nodes
"""

from __future__ import annotations

from typing import Iterator

import logging

from urllib.parse import urlencode
from jenkinsapi.node import Node
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.custom_exceptions import JenkinsAPIException
from jenkinsapi.custom_exceptions import UnknownNode
from jenkinsapi.custom_exceptions import PostRequired

log: logging.Logger = logging.getLogger(__name__)


class Nodes(JenkinsBase):
    """
    Class to hold information on a collection of nodes
    """

    def __init__(self, baseurl: str, jenkins_obj: "Jenkins") -> None:
        """
        Handy access to all of the nodes on your Jenkins server
        """
        self.jenkins = jenkins_obj
        JenkinsBase.__init__(
            self,
            (
                baseurl.rstrip("/")
                if "/computer" in baseurl
                else baseurl.rstrip("/") + "/computer"
            ),
        )

    def get_jenkins_obj(self) -> "Jenkins":
        return self.jenkins

    def __str__(self) -> str:
        return "Nodes @ %s" % self.baseurl

    def __contains__(self, node_name: str) -> bool:
        return node_name in self.keys()

    def iterkeys(self) -> Iterator[str]:
        """
        Return an iterator over the container's node names.

        Using iterkeys() while creating nodes may raise a RuntimeError
        or fail to iterate over all entries.
        """
        for item in self._data["computer"]:
            yield item["displayName"]

    def keys(self) -> list[str]:
        """
        Return a copy of the container's list of node names.
        """
        return list(self.iterkeys())

    def _make_node(self, nodename) -> Node:
        """
        Creates an instance of Node for the given nodename.
        This function assumes the returned node exists.
        """
        if nodename.lower() == "built-in node":
            nodeurl = "%s/(%s)" % (self.baseurl, "built-in")
        else:
            nodeurl = "%s/%s" % (self.baseurl, nodename)
        return Node(self.jenkins, nodeurl, nodename, node_dict={})

    def iteritems(self) -> Iterator[tuple[str, Node]]:
        """
        Return an iterator over the container's (name, node) pairs.

        Using iteritems() while creating nodes may raise a RuntimeError or
        fail to iterate over all entries.
        """
        for item in self._data["computer"]:
            nodename = item["displayName"]
            try:
                yield nodename, self._make_node(nodename)
            except Exception:
                raise JenkinsAPIException("Unable to iterate nodes")

    def items(self) -> list[tuple[str, Node]]:
        """
        Return a copy of the container's list of (name, node) pairs.
        """
        return list(self.iteritems())

    def itervalues(self) -> Iterator[Node]:
        """
        Return an iterator over the container's nodes.

        Using itervalues() while creating nodes may raise a RuntimeError
        or fail to iterate over all entries.
        """
        for item in self._data["computer"]:
            try:
                yield self._make_node(item["displayName"])
            except Exception:
                raise JenkinsAPIException("Unable to iterate nodes")

    def values(self) -> list[Node]:
        """
        Return a copy of the container's list of nodes.
        """
        return list(self.itervalues())

    def __getitem__(self, nodename: str) -> Node:
        if nodename in self:
            return self._make_node(nodename)
        raise UnknownNode(nodename)

    def __len__(self) -> int:
        return len(self.keys())

    def __delitem__(self, item: str) -> None:
        if item in self and item != "Built-In Node":
            url = "%s/doDelete" % self[item].baseurl
            try:
                self.jenkins.requester.get_and_confirm_status(url)
            except PostRequired:
                # Latest Jenkins requires POST here. GET kept for compatibility
                self.jenkins.requester.post_and_confirm_status(url, data={})
            self.poll()
        else:
            if item != "Built-In Node":
                raise UnknownNode("Node %s does not exist" % item)

            log.info("Requests to remove built-in node ignored")

    def __setitem__(self, name: str, node_dict: dict):
        if not isinstance(node_dict, dict):
            raise ValueError('"node_dict" parameter must be a Node dict')
        if name not in self:
            self.create_node(name, node_dict)
        self.poll()

    def create_node(self, name: str, node_dict: dict) -> Node:
        """
        Create a new slave node

        :param str name: name of slave
        :param dict node_dict: node dict (See Node class)
        :return: node obj
        """
        if name in self:
            return self[name]

        node = Node(
            jenkins_obj=self.jenkins,
            baseurl="",
            nodename=name,
            node_dict=node_dict,
            poll=False,
        )

        url = "%s/computer/doCreateItem?%s" % (
            self.jenkins.baseurl,
            urlencode(node.get_node_attributes()),
        )
        data = {"json": urlencode(node.get_node_attributes())}
        self.jenkins.requester.post_and_confirm_status(url, data=data)
        self.poll()
        return self[name]

    def create_node_with_config(self, name: str, config: dict) -> Node | None:
        """
        Create a new slave node with specific configuration.
        Config should be resemble the output of node.get_node_attributes()
        :param str name: name of slave
        :param dict config: Node attributes for Jenkins API request
            to create node
            (See function output Node.get_node_attributes())
        :return: node obj
        """
        if name in self:
            return self[name]

        if not isinstance(config, dict):
            return None
        url = "%s/computer/doCreateItem?%s" % (
            self.jenkins.baseurl,
            urlencode(config),
        )
        data = {"json": urlencode(config)}
        self.jenkins.requester.post_and_confirm_status(url, data=data)
        self.poll()
        return self[name]
