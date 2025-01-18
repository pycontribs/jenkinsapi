"""
Module for jenkinsapi Executer class
"""

from __future__ import annotations

from jenkinsapi.jenkinsbase import JenkinsBase
import logging

log = logging.getLogger(__name__)


class Executor(JenkinsBase):
    """
    Class to hold information on nodes that are attached as slaves to the
    master jenkins instance
    """

    def __init__(
        self, baseurl: str, nodename: str, jenkins_obj: "Jenkins", number: int
    ) -> None:
        """
        Init a node object by providing all relevant pointers to it
        :param baseurl: basic url for querying information on a node
        :param nodename: hostname of the node
        :param jenkins_obj: ref to the jenkins obj
        :return: Node obj
        """
        self.nodename: str = nodename
        self.number: int = number
        self.jenkins: "Jenkins" = jenkins_obj
        self.baseurl: str = baseurl
        JenkinsBase.__init__(self, baseurl)

    def __str__(self) -> str:
        return f"{self.nodename} {self.number}"

    def get_jenkins_obj(self) -> "Jenkins":
        return self.jenkins

    def get_progress(self) -> str:
        """Returns percentage"""
        return self.poll(tree="progress")["progress"]

    def get_number(self) -> int:
        """
        Get Executor number.
        """
        return self.poll(tree="number")["number"]

    def is_idle(self) -> bool:
        """
        Returns Boolean: whether Executor is idle or not.
        """
        return self.poll(tree="idle")["idle"]

    def likely_stuck(self) -> bool:
        """
        Returns Boolean: whether Executor is likely stuck or not.
        """
        return self.poll(tree="likelyStuck")["likelyStuck"]

    def get_current_executable(self) -> str:
        """
        Returns the current Queue.Task this executor is running.
        """
        return self.poll(tree="currentExecutable")["currentExecutable"]
