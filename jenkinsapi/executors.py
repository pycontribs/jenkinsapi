"""
This module implements the Executors class, which is intended to be a
container-like interface for all of the executors defined on a single
Jenkins node.
"""

from __future__ import annotations

import logging
from typing import Iterator

from jenkinsapi.executor import Executor
from jenkinsapi.jenkinsbase import JenkinsBase

log: logging.Logger = logging.getLogger(__name__)


class Executors(JenkinsBase):
    """
    This class provides a container-like API which gives
    access to all executors on a Jenkins node.

    Returns a list of Executor Objects.
    """

    def __init__(
        self, baseurl: str, nodename: str, jenkins: "Jenkins"
    ) -> None:
        self.nodename: str = nodename
        self.jenkins: str = jenkins
        JenkinsBase.__init__(self, baseurl)
        self.count: int = self._data["numExecutors"]

    def __str__(self) -> str:
        return f"Executors @ {self.baseurl}"

    def get_jenkins_obj(self) -> "Jenkins":
        return self.jenkins

    def __iter__(self) -> Iterator[Executor]:
        for index in range(self.count):
            executor_url = "%s/executors/%s" % (self.baseurl, index)
            yield Executor(executor_url, self.nodename, self.jenkins, index)
