from unittest import mock

import unittest

from jenkinsapi import config
from jenkinsapi.job import Job
from jenkinsapi.jenkinsbase import JenkinsBase


class TestJobGetAllBuilds(unittest.TestCase):
    # this job has builds
    JOB1_DATA = {
        "actions": [],
        "description": "test job",
        "displayName": "foo",
        "displayNameOrNull": None,
        "name": "foo",
        "url": "http://halob:8080/job/foo/",
        "buildable": True,
        # do as if build 1 & 2 are not returned by jenkins
        "builds": [{"number": 3, "url": "http://halob:8080/job/foo/3/"}],
        "color": "blue",
        "firstBuild": {"number": 1, "url": "http://halob:8080/job/foo/1/"},
        "healthReport": [
            {
                "description": "Build stability: No recent builds failed.",
                "iconUrl": "health-80plus.png",
                "score": 100,
            }
        ],
        "inQueue": False,
        "keepDependencies": False,
        # build running
        "lastBuild": {"number": 4, "url": "http://halob:8080/job/foo/4/"},
        "lastCompletedBuild": {
            "number": 3,
            "url": "http://halob:8080/job/foo/3/",
        },
        "lastFailedBuild": None,
        "lastStableBuild": {
            "number": 3,
            "url": "http://halob:8080/job/foo/3/",
        },
        "lastSuccessfulBuild": {
            "number": 3,
            "url": "http://halob:8080/job/foo/3/",
        },
        "lastUnstableBuild": None,
        "lastUnsuccessfulBuild": None,
        "nextBuildNumber": 4,
        "property": [],
        "queueItem": None,
        "concurrentBuild": False,
        "downstreamProjects": [],
        "scm": {},
        "upstreamProjects": [],
    }
    JOB1_ALL_BUILDS_DATA = {
        "allBuilds": [
            {"number": 3, "url": "http://halob:8080/job/foo/3/"},
            {"number": 2, "url": "http://halob:8080/job/foo/2/"},
            {"number": 1, "url": "http://halob:8080/job/foo/1/"},
        ],
    }
    JOB1_API_URL = "http://halob:8080/job/foo/%s" % config.JENKINS_API

    JOB2_DATA = {
        "actions": [],
        "buildable": True,
        "builds": [],
        "color": "notbuilt",
        "concurrentBuild": False,
        "description": "",
        "displayName": "look_ma_no_builds",
        "displayNameOrNull": None,
        "downstreamProjects": [],
        "firstBuild": None,
        "healthReport": [],
        "inQueue": False,
        "keepDependencies": False,
        "lastBuild": None,
        "lastCompletedBuild": None,
        "lastFailedBuild": None,
        "lastStableBuild": None,
        "lastSuccessfulBuild": None,
        "lastUnstableBuild": None,
        "lastUnsuccessfulBuild": None,
        "name": "look_ma_no_builds",
        "nextBuildNumber": 1,
        "property": [{}],
        "queueItem": None,
        "scm": {},
        "upstreamProjects": [],
        "url": "http://halob:8080/job/look_ma_no_builds/",
    }
    JOB2_API_URL = (
        "http://halob:8080/job/look_ma_no_builds/%s" % config.JENKINS_API
    )

    # Full list available immediatly
    JOB3_DATA = {
        "actions": [],
        "description": "test job",
        "displayName": "fullfoo",
        "displayNameOrNull": None,
        "name": "fullfoo",
        "url": "http://halob:8080/job/fullfoo/",
        "buildable": True,
        # all builds have been returned by Jenkins
        "builds": [
            {"number": 3, "url": "http://halob:8080/job/fullfoo/3/"},
            {"number": 2, "url": "http://halob:8080/job/fullfoo/2/"},
            {"number": 1, "url": "http://halob:8080/job/fullfoo/1/"},
        ],
        "color": "blue",
        "firstBuild": {"number": 1, "url": "http://halob:8080/job/fullfoo/1/"},
        "healthReport": [
            {
                "description": "Build stability: No recent builds failed.",
                "iconUrl": "health-80plus.png",
                "score": 100,
            }
        ],
        "inQueue": False,
        "keepDependencies": False,
        # build running
        "lastBuild": {"number": 4, "url": "http://halob:8080/job/fullfoo/4/"},
        "lastCompletedBuild": {
            "number": 3,
            "url": "http://halob:8080/job/fullfoo/3/",
        },
        "lastFailedBuild": None,
        "lastStableBuild": {
            "number": 3,
            "url": "http://halob:8080/job/fullfoo/3/",
        },
        "lastSuccessfulBuild": {
            "number": 3,
            "url": "http://halob:8080/job/fullfoo/3/",
        },
        "lastUnstableBuild": None,
        "lastUnsuccessfulBuild": None,
        "nextBuildNumber": 4,
        "property": [],
        "queueItem": None,
        "concurrentBuild": False,
        "downstreamProjects": [],
        "scm": {},
        "upstreamProjects": [],
    }
    JOB3_ALL_BUILDS_DATA = {
        "allBuilds": [
            {"number": 3, "url": "http://halob:8080/job/fullfoo/3/"},
            {"number": 2, "url": "http://halob:8080/job/fullfoo/2/"},
            {"number": 1, "url": "http://halob:8080/job/fullfoo/1/"},
        ],
    }
    JOB3_API_URL = "http://halob:8080/job/fullfoo/%s" % config.JENKINS_API

    URL_DATA = {
        JOB1_API_URL: JOB1_DATA,
        (JOB1_API_URL, "allBuilds[number,url]"): JOB1_ALL_BUILDS_DATA,
        JOB2_API_URL: JOB2_DATA,
        JOB3_API_URL: JOB3_DATA,
        # this one below should never be used
        (JOB3_API_URL, "allBuilds[number,url]"): JOB3_ALL_BUILDS_DATA,
    }

    def fakeGetData(self, url, params=None, tree=None):
        TestJobGetAllBuilds.__get_data_call_count += 1
        if params is None:
            try:
                return dict(TestJobGetAllBuilds.URL_DATA[url])
            except KeyError:
                raise Exception("Missing data for url: %s" % url)
        else:
            try:
                return dict(TestJobGetAllBuilds.URL_DATA[(url, str(params))])
            except KeyError:
                raise Exception(
                    "Missing data for url: %s with parameters %s"
                    % (url, repr(params))
                )

    def fakeGetDataTree(self, url, **args):
        TestJobGetAllBuilds.__get_data_call_count += 1
        try:
            if args["tree"]:
                if "builds" in args["tree"]:
                    return {
                        "builds": TestJobGetAllBuilds.URL_DATA[url]["builds"]
                    }
                elif "allBuilds" in args["tree"]:
                    return TestJobGetAllBuilds.URL_DATA[(url, args["tree"])]
                elif "lastBuild" in args["tree"]:
                    return {
                        "lastBuild": TestJobGetAllBuilds.URL_DATA[url][
                            "lastBuild"
                        ]
                    }
            else:
                return dict(TestJobGetAllBuilds.URL_DATA[url])
        except KeyError:
            raise Exception("Missing data for %s" % url)

    @mock.patch.object(JenkinsBase, "get_data", fakeGetDataTree)
    def setUp(self):
        TestJobGetAllBuilds.__get_data_call_count = 0
        self.J = mock.MagicMock()  # Jenkins object
        self.j = Job("http://halob:8080/job/foo/", "foo", self.J)

    @mock.patch.object(JenkinsBase, "get_data", fakeGetDataTree)
    def test_get_build_dict(self):
        # The job data contains only one build, so we expect that the
        # remaining jobs will be fetched automatically
        ret = self.j.get_build_dict()
        self.assertTrue(isinstance(ret, dict))
        self.assertEqual(len(ret), 4)

    @mock.patch.object(JenkinsBase, "get_data", fakeGetDataTree)
    def test_incomplete_builds_list_will_call_jenkins_twice(self):
        # The job data contains only one build, so we expect that the
        # remaining jobs will be fetched automatically, and to have two calls
        # to the Jenkins API
        TestJobGetAllBuilds.__get_data_call_count = 0
        self.J.lazy = False
        self.j = Job("http://halob:8080/job/foo/", "foo", self.J)
        self.assertEqual(TestJobGetAllBuilds.__get_data_call_count, 2)

    @mock.patch.object(JenkinsBase, "get_data", fakeGetDataTree)
    def test_lazy_builds_list_will_not_call_jenkins_twice(self):
        # The job data contains only one build, so we expect that the
        # remaining jobs will be fetched automatically, and to have two calls
        # to the Jenkins API
        TestJobGetAllBuilds.__get_data_call_count = 0
        self.J.lazy = True
        self.j = Job("http://halob:8080/job/foo/", "foo", self.J)
        self.assertEqual(TestJobGetAllBuilds.__get_data_call_count, 1)
        self.J.lazy = False

    @mock.patch.object(JenkinsBase, "get_data", fakeGetDataTree)
    def test_complete_builds_list_will_call_jenkins_once(self):
        # The job data contains all builds, so we will not gather remaining
        # builds
        TestJobGetAllBuilds.__get_data_call_count = 0
        self.j = Job("http://halob:8080/job/fullfoo/", "fullfoo", self.J)
        self.assertEqual(TestJobGetAllBuilds.__get_data_call_count, 1)

    @mock.patch.object(JenkinsBase, "get_data", fakeGetDataTree)
    def test_nobuilds_get_build_dict(self):
        j = Job(
            "http://halob:8080/job/look_ma_no_builds/",
            "look_ma_no_builds",
            self.J,
        )

        ret = j.get_build_dict()
        self.assertTrue(isinstance(ret, dict))
        self.assertEqual(len(ret), 0)

    @mock.patch.object(JenkinsBase, "get_data", fakeGetDataTree)
    def test_get_build_ids(self):
        # The job data contains only one build, so we expect that the
        # remaining jobs will be fetched automatically
        ret = list(self.j.get_build_ids())
        self.assertTrue(isinstance(ret, list))
        self.assertEqual(len(ret), 4)


if __name__ == "__main__":
    unittest.main()
