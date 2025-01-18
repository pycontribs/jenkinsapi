"""
Module for jenkinsapi Job
"""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
import urllib.parse as urlparse

from collections import defaultdict
from jenkinsapi.build import Build
from jenkinsapi.custom_exceptions import (
    NoBuildData,
    NotConfiguredSCM,
    NotFound,
    NotInQueue,
    NotSupportSCM,
    UnknownQueueItem,
    BadParams,
)
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.mutable_jenkins_thing import MutableJenkinsThing
from jenkinsapi.queue import QueueItem


SVN_URL = "./scm/locations/hudson.scm.SubversionSCM_-ModuleLocation/remote"
GIT_URL = "./scm/userRemoteConfigs/hudson.plugins.git.UserRemoteConfig/url"
HG_URL = "./scm/source"
GIT_BRANCH = "./scm/branches/hudson.plugins.git.BranchSpec/name"
HG_BRANCH = "./scm/branch"
DEFAULT_HG_BRANCH_NAME = "default"

log = logging.getLogger(__name__)


class Job(JenkinsBase, MutableJenkinsThing):
    """
    Represents a jenkins job
    A job can hold N builds which are the actual execution environments
    """

    def __init__(self, url: str, name: str, jenkins_obj: "Jenkins") -> None:
        self.name: str = name
        self.jenkins: "Jenkins" = jenkins_obj
        self._revmap = None
        self._config = None
        self._element_tree = None
        self._scm_prefix = ""
        self._scm_map = {
            "hudson.scm.SubversionSCM": "svn",
            "hudson.plugins.git.GitSCM": "git",
            "hudson.plugins.mercurial.MercurialSCM": "hg",
            "hudson.scm.NullSCM": "NullSCM",
        }
        self._scmurlmap = {
            "svn": lambda element_tree: list(element_tree.findall(SVN_URL)),
            "git": lambda element_tree: list(
                element_tree.findall(self._scm_prefix + GIT_URL)
            ),
            "hg": lambda element_tree: list(element_tree.findall(HG_URL)),
            None: lambda element_tree: [],
        }
        self._scmbranchmap = {
            "svn": lambda element_tree: [],
            "git": lambda element_tree: list(
                element_tree.findall(self._scm_prefix + GIT_BRANCH)
            ),
            "hg": self._get_hg_branch,
            None: lambda element_tree: [],
        }
        self.url: str = url
        JenkinsBase.__init__(self, self.url)

    def __str__(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self._data["description"]

    def get_jenkins_obj(self) -> "Jenkins":
        return self.jenkins

    # When the name of the hg branch used in the job is default hg branch (i.e.
    # default), Mercurial plugin doesn't store default branch name in
    # config XML file of the job. Create XML node corresponding to
    # default branch
    def _get_hg_branch(self, element_tree):
        branches = element_tree.findall(HG_BRANCH)
        if not branches:
            hg_default_branch = ET.Element("branch")
            hg_default_branch.text = DEFAULT_HG_BRANCH_NAME
            branches.append(hg_default_branch)
        return branches

    def poll(self, tree=None):
        data = super(Job, self).poll(tree=tree)
        if not tree and not self.jenkins.lazy:
            self._data = self._add_missing_builds(self._data)

        return data

    # pylint: disable=E1123
    # Unexpected keyword arg 'params'
    def _add_missing_builds(self, data):
        """
        Query Jenkins to get all builds of the job in the data object.

        Jenkins API loads the first 100 builds and thus may not contain
        all builds information. This method checks if all builds are loaded
        in the data object and updates it with the missing builds if needed.
        """
        if not data.get("builds"):
            return data
        # do not call _buildid_for_type here: it would poll and do an infinite
        # loop
        oldest_loaded_build_number = data["builds"][-1]["number"]
        if "firstBuild" not in self._data or not self._data["firstBuild"]:
            first_build_number = oldest_loaded_build_number
        else:
            first_build_number = self._data["firstBuild"]["number"]
        all_builds_loaded = oldest_loaded_build_number == first_build_number
        if all_builds_loaded:
            return data
        response = self.poll(tree="allBuilds[number,url]")
        data["builds"] = response["allBuilds"]
        return data

    def _get_config_element_tree(self):
        """
        The ElementTree objects creation is unnecessary, it can be
        a singleton per job
        """
        if self._config is None:
            self.load_config()

        if self._element_tree is None:
            self._element_tree = ET.fromstring(self._config)
        return self._element_tree

    def get_build_triggerurl(self) -> str:
        if not self.has_params():
            return "%s/build" % self.baseurl
        return "%s/buildWithParameters" % self.baseurl

    @staticmethod
    def _mk_json_from_build_parameters(build_params, file_params=None):
        """
        Build parameters must be submitted in a particular format
        Key-Value pairs would be far too simple, no no!
        Watch and read on and behold!
        """
        if not isinstance(build_params, dict):
            raise ValueError("Build parameters must be a dict")

        build_p = [
            {"name": k, "value": v} for k, v in sorted(build_params.items())
        ]

        out = {"parameter": build_p}
        if file_params:
            file_p = [{"name": k, "file": k} for k in file_params.keys()]
            out["parameter"].extend(file_p)

        if len(out["parameter"]) == 1:
            out["parameter"] = out["parameter"][0]

        return out

    @staticmethod
    def mk_json_from_build_parameters(build_params, file_params=None):
        json_structure = Job._mk_json_from_build_parameters(
            build_params, file_params
        )
        json_structure["statusCode"] = "303"
        json_structure["redirectTo"] = "."
        return json.dumps(json_structure)

    def invoke(
        self,
        securitytoken=None,
        block: bool = False,
        build_params=None,
        cause=None,
        files=None,
        delay: int = 5,
        quiet_period=None,
    ) -> QueueItem:
        assert isinstance(block, bool)
        if build_params and (not self.has_params()):
            raise BadParams("This job does not support parameters")

        params = {}  # Via Get string

        if securitytoken:
            params["token"] = securitytoken

        # Either copy the params dict or make a new one.
        build_params = (
            dict(build_params.items()) if build_params else {}
        )  # Via POSTed JSON

        url = self.get_build_triggerurl()
        # If quiet period is set, the build will have {quiet_period} seconds
        # quiet peroid before start.
        if quiet_period is not None:
            url += "?delay={0}sec".format(quiet_period)
        if cause:
            build_params["cause"] = cause

        # Build require params as form fields
        # and as Json.
        data = {
            "json": self.mk_json_from_build_parameters(build_params, files)
        }
        data.update(build_params)

        response = self.jenkins.requester.post_and_confirm_status(
            url,
            data=data,
            params=params,
            files=files,
            valid=[200, 201, 303],
            allow_redirects=False,
        )

        redirect_url = response.headers["location"]

        #
        # Enterprise Jenkins implementations such as CloudBees locate their
        # queue REST API base https://server.domain.com/jenkins/queue/api/
        # above the team-specific REST API base
        # https://server.domain.com/jenkins/job/my_team/api/
        #
        queue_baseurl_candidates = [self.jenkins.baseurl]
        scheme, netloc, path, _, query, frag = urlparse.urlparse(
            self.jenkins.baseurl
        )
        while path:
            path = "/".join(path.rstrip("/").split("/")[:-1])
            queue_baseurl_candidates.append(
                urlparse.urlunsplit([scheme, netloc, path, query, frag])
            )
        redirect_url_valid = False
        for queue_baseurl_candidate in queue_baseurl_candidates:
            redirect_url_valid = redirect_url.startswith(
                "%s/queue/item" % queue_baseurl_candidate
            )
            if redirect_url_valid:
                break
        if not redirect_url_valid:
            raise ValueError("Not a Queue URL: %s" % redirect_url)

        qi = QueueItem(redirect_url, self.jenkins)
        if block:
            qi.block_until_complete(delay=delay)
        return qi

    def _buildid_for_type(self, buildtype):
        """
        Gets a buildid for a given type of build
        """
        KNOWNBUILDTYPES = [
            "lastStableBuild",
            "lastSuccessfulBuild",
            "lastBuild",
            "lastCompletedBuild",
            "firstBuild",
            "lastFailedBuild",
        ]
        assert buildtype in KNOWNBUILDTYPES, (
            "Unknown build info type: %s" % buildtype
        )

        data = self.poll(tree="%s[number]" % buildtype)

        if not data.get(buildtype):
            raise NoBuildData(buildtype)
        return data[buildtype]["number"]

    def get_first_buildnumber(self):
        """
        Get the numerical ID of the first build.
        """
        return self._buildid_for_type("firstBuild")

    def get_last_stable_buildnumber(self):
        """
        Get the numerical ID of the last stable build.
        """
        return self._buildid_for_type("lastStableBuild")

    def get_last_good_buildnumber(self):
        """
        Get the numerical ID of the last good build.
        """
        return self._buildid_for_type("lastSuccessfulBuild")

    def get_last_failed_buildnumber(self):
        """
        Get the numerical ID of the last failed build.
        """
        return self._buildid_for_type(buildtype="lastFailedBuild")

    def get_last_buildnumber(self):
        """
        Get the numerical ID of the last build.
        """
        return self._buildid_for_type("lastBuild")

    def get_last_completed_buildnumber(self):
        """
        Get the numerical ID of the last complete build.
        """
        return self._buildid_for_type("lastCompletedBuild")

    def get_build_dict(self):
        builds = self.poll(tree="builds[number,url]")
        if not builds:
            raise NoBuildData(repr(self))
        builds = self._add_missing_builds(builds)
        builds = builds["builds"]
        last_build = self.poll(tree="lastBuild[number,url]")["lastBuild"]
        if (
            builds
            and last_build
            and builds[0]["number"] != last_build["number"]
        ):
            builds = [last_build] + builds
        # FIXME SO how is this supposed to work if build is false-y?
        # I don't think that builds *can* be false here, so I don't
        # understand the test above.
        return dict((build["number"], build["url"]) for build in builds)

    def get_build_by_params(self, build_params, order=1):
        first_build_number = self.get_first_buildnumber()
        last_build_number = self.get_last_buildnumber()
        if order != 1 and order != -1:
            raise ValueError(
                "Direction should be ascending or descending (1/-1)"
            )

        for number in range(first_build_number, last_build_number + 1)[
            ::order
        ]:
            build = self.get_build(number)
            if build.get_params() == build_params:
                return build

        raise NoBuildData(
            "No build with such params {params}".format(params=build_params)
        )

    def get_revision_dict(self):
        """
        Get dictionary of all revisions with a list of buildnumbers (int)
        that used that particular revision
        """
        revs = defaultdict(list)
        if "builds" not in self._data:
            raise NoBuildData(repr(self))
        for buildnumber in self.get_build_ids():
            revs[self.get_build(buildnumber).get_revision()].append(
                buildnumber
            )
        return revs

    def get_build_ids(self):
        """
        Return a sorted list of all good builds as ints.
        """
        return reversed(sorted(self.get_build_dict().keys()))

    def get_next_build_number(self):
        """
        Return the next build number that Jenkins will assign.
        """
        return self._data.get("nextBuildNumber", 0)

    def get_last_stable_build(self):
        """
        Get the last stable build
        """
        bn = self.get_last_stable_buildnumber()
        return self.get_build(bn)

    def get_last_good_build(self):
        """
        Get the last good build
        """
        bn = self.get_last_good_buildnumber()
        return self.get_build(bn)

    def get_last_build(self):
        """
        Get the last build
        """
        bn = self.get_last_buildnumber()
        return self.get_build(bn)

    def get_first_build(self):
        bn = self.get_first_buildnumber()
        return self.get_build(bn)

    def get_last_build_or_none(self):
        """
        Get the last build or None if there is no builds
        """
        try:
            return self.get_last_build()
        except NoBuildData:
            return None

    def get_last_completed_build(self):
        """
        Get the last build regardless of status
        """
        bn = self.get_last_completed_buildnumber()
        return self.get_build(bn)

    def get_buildnumber_for_revision(self, revision, refresh=False):
        """

        :param revision: subversion revision to look for, int
        :param refresh: boolean, whether or not to refresh the
            revision -> buildnumber map
        :return: list of buildnumbers, [int]
        """
        if self.get_scm_type() == "svn" and not isinstance(revision, int):
            revision = int(revision)
        if self._revmap is None or refresh:
            self._revmap = self.get_revision_dict()
        try:
            return self._revmap[revision]
        except KeyError:
            raise NotFound("Couldn't find a build with that revision")

    def get_build(self, buildnumber):
        assert isinstance(buildnumber, int)
        try:
            url = self.get_build_dict()[buildnumber]
            return Build(url, buildnumber, job=self)
        except KeyError:
            raise NotFound("Build #%s not found" % buildnumber)

    def delete_build(self, build_number):
        """
        Remove build

        :param int build_number:    Build number
        :raises NotFound:           When build is not found
        """
        try:
            url = self.get_build_dict()[build_number]
            url = "%s/doDelete" % url
            self.jenkins.requester.post_and_confirm_status(url, data="")
            self.jenkins.poll()
        except KeyError:
            raise NotFound("Build #%s not found" % build_number)

    def get_build_metadata(self, buildnumber):
        """
        Get the build metadata for a given build number. For large builds with
        tons of tests, this method is faster than get_build by returning less
        data.
        """
        if not isinstance(buildnumber, int):
            raise ValueError('Parameter "buildNumber" must be int')

        try:
            url = self.get_build_dict()[buildnumber]
            return Build(url, buildnumber, job=self, depth=0)
        except KeyError:
            raise NotFound("Build #%s not found" % buildnumber)

    def __delitem__(self, build_number):
        self.delete_build(build_number)

    def __getitem__(self, buildnumber):
        return self.get_build(buildnumber)

    def __len__(self):
        return len(self.get_build_dict())

    def is_queued_or_running(self):
        return self.is_queued() or self.is_running()

    def is_queued(self):
        data = self.poll(tree="inQueue")
        return data.get("inQueue", False)

    def get_queue_item(self):
        """
        Return a QueueItem if this object is in a queue, otherwise raise
        an exception
        """
        if not self.is_queued():
            raise UnknownQueueItem()
        q_item = self.poll(tree="queueItem[url]")
        qi_url = urlparse.urljoin(
            self.jenkins.baseurl, q_item["queueItem"]["url"]
        )
        return QueueItem(qi_url, self.jenkins)

    def is_running(self):
        # self.poll()
        try:
            build = self.get_last_build_or_none()
            if build is not None:
                return build.is_running()
        except NoBuildData:
            log.info(
                "No build info available for %s, assuming not running.",
                str(self),
            )
        return False

    def get_config(self):
        """
        Returns the config.xml from the job
        """
        response = self.jenkins.requester.get_and_confirm_status(
            "%(baseurl)s/config.xml" % self.__dict__
        )
        return response.text

    def load_config(self):
        self._config = self.get_config()

    def get_scm_type(self):
        element_tree = self._get_config_element_tree()
        scm_element = element_tree.find("scm")
        if not scm_element:
            multibranch_scm_prefix = "properties/org.jenkinsci.plugins.\
                    workflow.multibranch.BranchJobProperty/branch/"
            multibranch_path = multibranch_scm_prefix + "scm"
            scm_element = element_tree.find(multibranch_path)
            if scm_element:
                # multibranch pipeline.
                self._scm_prefix = multibranch_scm_prefix
        scm_class = scm_element.get("class") if scm_element else None
        scm = self._scm_map.get(scm_class)
        if not scm:
            raise NotSupportSCM(
                'SCM class "%s" not supported by API for job "%s"'
                % (scm_class, self.name)
            )
        if scm == "NullSCM":
            raise NotConfiguredSCM(
                'SCM is not configured for job "%s"' % self.name
            )
        return scm

    def get_scm_url(self):
        """
        Get list of project SCM urls
        For some SCM's jenkins allow to configure and use number of SCM url's
        : return: list of SCM urls
        """
        element_tree = self._get_config_element_tree()
        scm = self.get_scm_type()
        scm_url_list = [
            scm_url.text for scm_url in self._scmurlmap[scm](element_tree)
        ]
        return scm_url_list

    def get_scm_branch(self):
        """
        Get list of SCM branches
        : return: list of SCM branches
        """
        element_tree = self._get_config_element_tree()
        scm = self.get_scm_type()
        return [
            scm_branch.text
            for scm_branch in self._scmbranchmap[scm](element_tree)
        ]

    def modify_scm_branch(self, new_branch, old_branch=None):
        """
        Modify SCM ("Source Code Management") branch name for configured job.
        :param new_branch : new repository branch name to set.
            If job has multiple branches configured and "old_branch"
            not provided - method will allways modify first url.
        :param old_branch (optional): exact value of branch name
            to be replaced.
            For some SCM's jenkins allow set multiple branches per job
            this parameter intended to indicate which branch need to be
            modified
        """
        element_tree = self._get_config_element_tree()
        scm = self.get_scm_type()
        scm_branch_list = self._scmbranchmap[scm](element_tree)
        if scm_branch_list and not old_branch:
            scm_branch_list[0].text = new_branch
            self.update_config(ET.tostring(element_tree))
        else:
            for scm_branch in scm_branch_list:
                if scm_branch.text == old_branch:
                    scm_branch.text = new_branch
                    self.update_config(ET.tostring(element_tree))

    def modify_scm_url(self, new_source_url, old_source_url=None):
        """
        Modify SCM ("Source Code Management") url for configured job.
        :param new_source_url : new repository url to set.
            If job has multiple repositories configured and "old_source_url"
            not provided - method will allways modify first url.
        :param old_source_url (optional): for some SCM's jenkins allows
            settting multiple repositories per job
            this parameter intended to indicate which repository need
            to be modified
        """
        element_tree = self._get_config_element_tree()
        scm = self.get_scm_type()
        scm_url_list = self._scmurlmap[scm](element_tree)
        if scm_url_list and not old_source_url:
            scm_url_list[0].text = new_source_url
            self.update_config(ET.tostring(element_tree))
        else:
            for scm_url in scm_url_list:
                if scm_url.text == old_source_url:
                    scm_url.text = new_source_url
                    self.update_config(ET.tostring(element_tree))

    def get_config_xml_url(self):
        return "%s/config.xml" % self.baseurl

    def update_config(self, config, full_response=False, encoding="utf-8"):
        """
        Update the config.xml to the job
        Also refresh the ElementTree object since the config has changed
        :param full_response (optional): if True, it will return the full
            response object instead of just the response text.
            Useful for debugging and validation workflows.
        """
        url = self.get_config_xml_url()
        config = str(config)  # cast unicode in case of Python 2
        response = self.jenkins.requester.post_url(
            url, params={}, data=config.encode(encoding)
        )
        self._element_tree = ET.fromstring(config)

        if full_response:
            return response

        return response.text

    def get_downstream_jobs(self):
        """
        Get all the possible downstream jobs
        :return List of Job
        """
        downstream_jobs = []
        try:
            for j in self._data["downstreamProjects"]:
                downstream_jobs.append(self.get_jenkins_obj()[j["name"]])
        except KeyError:
            return []
        return downstream_jobs

    def get_downstream_job_names(self):
        """
        Get all the possible downstream job names
        :return List of String
        """
        downstream_jobs = []
        try:
            for j in self._data["downstreamProjects"]:
                downstream_jobs.append(j["name"])
        except KeyError:
            return []
        return downstream_jobs

    def get_upstream_job_names(self):
        """
        Get all the possible upstream job names
        :return List of String
        """
        upstream_jobs = []
        try:
            for j in self._data["upstreamProjects"]:
                upstream_jobs.append(j["name"])
        except KeyError:
            return []
        return upstream_jobs

    def get_upstream_jobs(self):
        """
        Get all the possible upstream jobs
        :return List of Job
        """
        upstream_jobs = []
        try:
            for j in self._data["upstreamProjects"]:
                upstream_jobs.append(self.get_jenkins_obj().get_job(j["name"]))
        except KeyError:
            return []
        return upstream_jobs

    def is_enabled(self):
        data = self.poll(tree="color")
        return "disabled" not in data.get("color", "")

    def disable(self):
        """
        Disable job
        """
        url = "%s/disable" % self.baseurl
        return self.get_jenkins_obj().requester.post_url(url, data="")

    def enable(self):
        """
        Enable job
        """
        url = "%s/enable" % self.baseurl
        return self.get_jenkins_obj().requester.post_url(url, data="")

    def delete_from_queue(self):
        """
        Delete a job from the queue only if it's enqueued
        :raise NotInQueue if the job is not in the queue
        """
        if not self.is_queued():
            raise NotInQueue()
        queue_id = self._data["queueItem"]["id"]
        url = urlparse.urljoin(
            self.get_jenkins_obj().get_queue().baseurl,
            "queue/cancelItem?id=%s" % queue_id,
        )
        self.get_jenkins_obj().requester.post_and_confirm_status(url, data="")
        return True

    def get_params(self):
        """
        Get the parameters for this job. Format varies by parameter type. Here
        is an example string parameter:
            {
                'type': 'StringParameterDefinition',
                'description': 'Parameter description',
                'defaultParameterValue': {'value': 'default value'},
                'name': 'FOO_BAR'
            }
        """
        places = ["actions", "property"]
        found_definitions = False

        for place in places:
            if found_definitions:
                return
            actions = (x for x in self._data[place] if x is not None)
            for action in actions:
                try:
                    for param in action["parameterDefinitions"]:
                        found_definitions = True
                        yield param
                except KeyError:
                    continue

    def get_params_list(self):
        """
        Gets the list of parameter names for this job.
        """
        return [param["name"] for param in self.get_params()]

    def has_params(self):
        """
        If job has parameters, returns True, else False
        """
        if any(
            "parameterDefinitions" in a for a in (self._data["actions"]) if a
        ):
            return True
        if any(
            "parameterDefinitions" in a for a in (self._data["property"]) if a
        ):
            return True
        return False

    def has_queued_build(self, build_params):
        """
        Returns True if a build with build_params is currently queued.
        """
        queue = self.jenkins.get_queue()
        queued_builds = queue.get_queue_items_for_job(self.name)
        for build in queued_builds:
            if build.get_parameters() == build_params:
                return True
        return False

    @staticmethod
    def get_full_name_from_url_and_baseurl(url, baseurl):
        """
        Get the full name for a job (including parent folders) from the
        job URL.
        """
        path = url.replace(baseurl, "")
        split = path.split("/")
        split = [urlparse.unquote(part) for part in split[::2] if part]
        return "/".join(split)

    def get_full_name(self):
        """
        Get the full name for a job (including parent folders)
        from the job URL.
        """
        return Job.get_full_name_from_url_and_baseurl(
            self.url, self.jenkins.baseurl
        )

    def toggle_keep_build(self, build_number):
        self.get_build(build_number).toggle_keep()
