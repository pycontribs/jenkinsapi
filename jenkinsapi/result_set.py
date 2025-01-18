"""
Module for jenkinsapi ResultSet
"""

from __future__ import annotations

from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.result import Result


class ResultSet(JenkinsBase):
    """
    Represents a result from a completed Jenkins run.
    """

    def __init__(self, url: str, build: "Build") -> None:
        """
        Init a resultset
        :param url: url for a build, str
        :param build: build obj
        """
        self.build: "Build" = build
        JenkinsBase.__init__(self, url)

    def get_jenkins_obj(self) -> "Jenkins":
        return self.build.job.get_jenkins_obj()

    def __str__(self) -> str:
        return "Test Result for %s" % str(self.build)

    @property
    def name(self):
        return str(self)

    def keys(self) -> list[str]:
        return [a[0] for a in self.iteritems()]

    def items(self):
        return [a for a in self.iteritems()]

    def iteritems(self):
        for suite in self._data.get("suites", []):
            for case in suite["cases"]:
                result = Result(**case)
                yield result.identifier(), result

        for report_set in self._data.get("childReports", []):
            if report_set["result"]:
                for suite in report_set["result"]["suites"]:
                    for case in suite["cases"]:
                        result = Result(**case)
                        yield result.identifier(), result

    def __len__(self):
        return len(self.items())

    def __getitem__(self, key):
        self_as_dict = dict(self.iteritems())
        return self_as_dict[key]
