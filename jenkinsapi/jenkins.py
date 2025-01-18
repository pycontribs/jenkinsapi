"""
Module for jenkinsapi Jenkins object
"""

from __future__ import annotations

import time
import logging
import warnings

from urllib.parse import urlparse
from urllib.request import Request, HTTPRedirectHandler, build_opener
from urllib.parse import quote as urlquote
from urllib.parse import urlencode

from requests import HTTPError, ConnectionError

from jenkinsapi import config
from jenkinsapi.credentials import Credentials
from jenkinsapi.credentials import Credentials2x
from jenkinsapi.credentials import CredentialsById
from jenkinsapi.executors import Executors
from jenkinsapi.jobs import Jobs
from jenkinsapi.job import Job
from jenkinsapi.view import View
from jenkinsapi.label import Label
from jenkinsapi.node import Node
from jenkinsapi.nodes import Nodes
from jenkinsapi.plugins import Plugins
from jenkinsapi.plugin import Plugin
from jenkinsapi.utils.requester import Requester
from jenkinsapi.views import Views
from jenkinsapi.queue import Queue
from jenkinsapi.fingerprint import Fingerprint
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.custom_exceptions import JenkinsAPIException
from jenkinsapi.utils.crumb_requester import CrumbRequester


log = logging.getLogger(__name__)


class Jenkins(JenkinsBase):
    """
    Represents a jenkins environment.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        baseurl: str,
        username: str = "",
        password: str = "",
        requester=None,
        lazy: bool = False,
        ssl_verify: bool = True,
        cert=None,
        timeout: int = 10,
        use_crumb: bool = True,
        max_retries=None,
    ) -> None:
        """
        :param baseurl: baseurl for jenkins instance including port, str
        :param username: username for jenkins auth, str
        :param password: password for jenkins auth, str
        :return: a Jenkins obj
        """
        self.username = username
        self.password = password
        if requester is None:
            if use_crumb:
                requester = CrumbRequester
            else:
                requester = Requester

            self.requester = requester(
                username,
                password,
                baseurl=baseurl,
                ssl_verify=ssl_verify,
                cert=cert,
                timeout=timeout,
                max_retries=max_retries,
            )
        else:
            self.requester = requester

        self.requester.timeout = timeout
        self.lazy = lazy
        self.jobs_container = None
        JenkinsBase.__init__(self, baseurl, poll=not lazy)

    def _poll(self, tree=None):
        url = self.python_api_url(self.baseurl)
        return self.get_data(
            url, tree="jobs[name,color,url]" if not tree else tree
        )

    def _poll_if_needed(self):
        if self.lazy and self._data is None:
            self.poll()

    def _clone(self):
        return Jenkins(
            self.baseurl,
            username=self.username,
            password=self.password,
            requester=self.requester,
        )

    def base_server_url(self):
        if config.JENKINS_API in self.baseurl:
            return self.baseurl[: -(len(config.JENKINS_API))]
        return self.baseurl

    def validate_fingerprint(self, id_):
        obj_fingerprint = Fingerprint(self.baseurl, id_, jenkins_obj=self)
        obj_fingerprint.validate()
        log.info(msg="Jenkins says %s is valid" % id_)

    def get_artifact_data(self, id_):
        obj_fingerprint = Fingerprint(self.baseurl, id_, jenkins_obj=self)
        obj_fingerprint.validate()
        return obj_fingerprint.get_info()

    def validate_fingerprint_for_build(self, digest, filename, job, build):
        obj_fingerprint = Fingerprint(self.baseurl, digest, jenkins_obj=self)
        return obj_fingerprint.validate_for_build(filename, job, build)

    def get_jenkins_obj(self):
        return self

    def get_jenkins_obj_from_url(self, url: str):
        return Jenkins(url, self.username, self.password, self.requester)

    def get_create_url(self) -> str:
        # This only ever needs to work on the base object
        return "%s/createItem" % self.baseurl

    def get_nodes_url(self) -> str:
        # This only ever needs to work on the base object
        return self.nodes.baseurl

    @property
    def jobs(self):
        if self.jobs_container is None:
            self.jobs_container = Jobs(self)

        return self.jobs_container

    def get_jobs(self):
        """
        Fetch all the build-names on this Jenkins server.
        """
        return self.jobs.iteritems()

    def get_jobs_info(self):
        """
        Get the jobs information
        :return url, name
        """
        for name, job in self.jobs.iteritems():
            yield job.url, name

    def get_job(self, jobname: str) -> Job:
        """
        Get a job by name
        :param jobname: name of the job, str
        :return: Job obj
        """
        return self.jobs[jobname]

    def get_job_by_url(self, url: str, job_name: str) -> Job:
        """
        Get a job by url
        :param url: jobs' url
        :param jobname: name of the job, str
        :return: Job obj
        """
        return Job(url, job_name, self)

    def has_job(self, jobname: str) -> bool:
        """
        Does a job by the name specified exist
        :param jobname: string
        :return: boolean
        """
        return jobname in self.jobs

    def create_job(self, jobname: str, xml) -> Job:
        """
        Create a job

        alternatively you can create job using Jobs object:
        self.jobs['job_name'] = config
        :param jobname: name of new job, str
        :param config: configuration of new job, xml
        :return: new Job obj
        """
        return self.jobs.create(jobname, xml)

    def create_multibranch_pipeline_job(
        self, jobname, xml, block=True, delay=60
    ):
        """
        :return: list of new Job objects
        """
        return self.jobs.create_multibranch_pipeline(
            jobname, xml, block, delay
        )

    def copy_job(self, jobname: str, newjobname: str) -> Job:
        return self.jobs.copy(jobname, newjobname)

    def build_job(self, jobname: str, params=None) -> None:
        """
        Invoke a build by job name
        :param jobname: name of exist job, str
        :param params: the job params, dict
        :return: none
        """
        self[jobname].invoke(build_params=params or {})

    def delete_job(self, jobname: str) -> None:
        """
        Delete a job by name
        :param jobname: name of a exist job, str
        :return: new jenkins_obj
        """
        del self.jobs[jobname]

    def rename_job(self, jobname: str, newjobname: str) -> Job:
        """
        Rename a job
        :param jobname: name of a exist job, str
        :param newjobname: name of new job, str
        :return: new Job obj
        """
        return self.jobs.rename(jobname, newjobname)

    def items(self):
        """
        :param return: A list of pairs.
            Each pair will be (job name, Job object)
        """
        return list(self.iteritems())

    def get_jobs_list(self):
        return self.jobs.keys()

    def iterkeys(self):
        return self.jobs.iterkeys()

    def iteritems(self):
        return self.jobs.iteritems()

    def keys(self):
        return self.jobs.keys()

    def __str__(self) -> str:
        return "Jenkins server at %s" % self.baseurl

    @property
    def views(self):
        return Views(self)

    def get_view_by_url(self, view_url: str):
        # for nested view
        view_name = view_url.split("/view/")[-1].replace("/", "")
        return View(view_url, view_name, jenkins_obj=self)

    def delete_view_by_url(self, viewurl: str):
        url = f"{viewurl}/doDelete"
        self.requester.post_and_confirm_status(url, data="")
        self.poll()
        return self

    def get_label(self, label_name: str) -> Label:
        label_url = "%s/label/%s" % (self.baseurl, label_name)
        return Label(label_url, label_name, jenkins_obj=self)

    def __getitem__(self, jobname: str) -> Job:
        """
        Get a job by name
        :param jobname: name of job, str
        :return: Job obj
        """
        return self.jobs[jobname]

    def __len__(self) -> int:
        return len(self.jobs)

    def __contains__(self, jobname: str) -> bool:
        """
        Does a job by the name specified exist
        :param jobname: string
        :return: boolean
        """
        return jobname in self.jobs

    def __delitem__(self, job_name: str) -> None:
        del self.jobs[job_name]

    def get_node(self, nodename: str) -> Node:
        """Get a node object for a specific node"""
        return self.nodes[nodename]

    def get_node_url(self, nodename: str = "") -> str:
        """Return the url for nodes"""
        url = urlparse.urljoin(
            self.base_server_url(), "computer/%s" % urlquote(nodename)
        )
        return url

    def get_queue_url(self):
        url = f"{self.base_server_url()}/queue"
        return url

    def get_queue(self) -> Queue:
        queue_url = self.get_queue_url()
        return Queue(queue_url, self)

    def get_nodes(self) -> Nodes:
        return Nodes(self.baseurl, self)

    @property
    def nodes(self):
        return self.get_nodes()

    def has_node(self, nodename: str) -> bool:
        """
        Does a node by the name specified exist
        :param nodename: string, hostname
        :return: boolean
        """
        self.poll()
        return nodename in self.nodes

    def delete_node(self, nodename: str) -> None:
        """
        Remove a node from the managed slave list
        Please note that you cannot remove the master node

        :param nodename: string holding a hostname
        :return: None
        """
        del self.nodes[nodename]

    def create_node(
        self,
        name: str,
        num_executors: int = 2,
        node_description: str = "",
        remote_fs: str = "/var/lib/jenkins",
        labels=None,
        exclusive: bool = False,
    ) -> Node:
        """
        Create a new JNLP slave node by name.

        To create SSH node, please see description in Node class

        :param name: fqdn of slave, str
        :param num_executors: number of executors, int
        :param node_description: a freetext field describing the node
        :param remote_fs: jenkins path, str
        :param labels: labels to associate with slave, str
        :param exclusive: tied to specific job, boolean
        :return: node obj
        """
        node_dict = {
            "num_executors": num_executors,
            "node_description": node_description,
            "remote_fs": remote_fs,
            "labels": labels,
            "exclusive": exclusive,
        }
        return self.nodes.create_node(name, node_dict)

    def create_node_with_config(self, name: str, config) -> Node | None:
        """
        Create a new slave node with specific configuration.
        Config should be resemble the output of node.get_node_attributes()
        :param str name: name of slave
        :param dict config: Node attributes for Jenkins API request
            to create node
            (See function output Node.get_node_attributes())
        :return: node obj
        """
        return self.nodes.create_node_with_config(name=name, config=config)

    def get_plugins_url(self, depth):
        # This only ever needs to work on the base object
        return f"{self.baseurl}/pluginManager/api/python?depth={depth}"

    def install_plugin(
        self,
        plugin: str | Plugin,
        restart: bool = True,
        force_restart: bool = False,
        wait_for_reboot: bool = True,
        no_reboot_warning: bool = False,
    ):
        """
        Install a plugin and optionally restart jenkins.
        @param plugin: Plugin (string or Plugin object) to be installed
        @param restart: Boolean, restart Jenkins when required by plugin
        @param force_restart: Boolean, force Jenkins to restart,
            ignoring plugin preferences
        @param no_warning: Don't show warning when restart is needed and
        restart parameters are set to False
        """
        if not isinstance(plugin, Plugin):
            plugin = Plugin(plugin)
        self.plugins[plugin.shortName] = plugin
        if force_restart or (restart and self.plugins.restart_required):
            self.safe_restart(wait_for_reboot=wait_for_reboot)
        elif self.plugins.restart_required and not no_reboot_warning:
            warnings.warn(
                "System reboot is required, but automatic reboot is disabled. "
                "Please reboot manually."
            )

    def install_plugins(
        self,
        plugin_list,
        restart: bool = True,
        force_restart: bool = False,
        wait_for_reboot: bool = True,
        no_reboot_warning: bool = False,
    ) -> None:
        """
        Install a list of plugins and optionally restart jenkins.
        @param plugin_list: List of plugins (strings, Plugin objects or
            a mix of the two) to be installed
        @param restart: Boolean, restart Jenkins when required by plugin
        @param force_restart: Boolean, force Jenkins to restart,
            ignoring plugin preferences
        """
        plugins = [
            p if isinstance(p, Plugin) else Plugin(p) for p in plugin_list
        ]
        for plugin in plugins:
            self.install_plugin(plugin, restart=False, no_reboot_warning=True)
        if force_restart or (restart and self.plugins.restart_required):
            self.safe_restart(wait_for_reboot=wait_for_reboot)
        elif self.plugins.restart_required and not no_reboot_warning:
            warnings.warn(
                "System reboot is required, but automatic reboot is disabled. "
                "Please reboot manually."
            )

    def delete_plugin(
        self,
        plugin: str | Plugin,
        restart: bool = True,
        force_restart: bool = False,
        wait_for_reboot: bool = True,
        no_reboot_warning: bool = False,
    ) -> None:
        """
        Delete a plugin and optionally restart jenkins. Will not delete
        dependencies.
        @param plugin: Plugin (string or Plugin object) to be deleted
        @param restart: Boolean, restart Jenkins when required by plugin
        @param force_restart: Boolean, force Jenkins to restart,
            ignoring plugin preferences
        """
        if isinstance(plugin, Plugin):
            plugin = plugin.shortName
        del self.plugins[plugin]
        if force_restart or (restart and self.plugins.restart_required):
            self.safe_restart(wait_for_reboot=wait_for_reboot)
        elif self.plugins.restart_required and not no_reboot_warning:
            warnings.warn(
                "System reboot is required, but automatic reboot is disabled. "
                "Please reboot manually."
            )

    def delete_plugins(
        self,
        plugin_list,
        restart: bool = True,
        force_restart: bool = False,
        wait_for_reboot: bool = True,
        no_reboot_warning: bool = False,
    ):
        """
        Delete a list of plugins and optionally restart jenkins. Will not
        delete dependencies.
        @param plugin_list: List of plugins (strings, Plugin objects or
            a mix of the two) to be deleted
        @param restart: Boolean, restart Jenkins when required by plugin
        @param force_restart: Boolean, force Jenkins to restart,
            ignoring plugin preferences
        """
        for plugin in plugin_list:
            self.delete_plugin(plugin, restart=False, no_reboot_warning=True)
        if force_restart or (restart and self.plugins.restart_required):
            self.safe_restart(wait_for_reboot=wait_for_reboot)
        elif self.plugins.restart_required and not no_reboot_warning:
            warnings.warn(
                "System reboot is required, but automatic reboot is disabled. "
                "Please reboot manually."
            )

    def safe_restart(self, wait_for_reboot: bool = True):
        """restarts jenkins when no jobs are running"""
        # NB: unlike other methods, the value of resp.status_code
        # here can be 503 even when everything is normal
        url = "%s/safeRestart" % (self.baseurl,)
        valid = self.requester.VALID_STATUS_CODES + [503, 500]
        resp = self.requester.post_and_confirm_status(
            url, data="", valid=valid
        )
        if wait_for_reboot:
            self._wait_for_reboot()
        return resp

    def _wait_for_reboot(self) -> None:
        # We need to make sure all jobs have finished,
        # and that jenkins is actually restarting.
        # One way to be sure is to make sure jenkins is really down.
        wait = 5
        count = 0
        max_count = 30
        self.__jenkins_is_unavailable()  # Blocks until jenkins is restarting
        while count < max_count:
            time.sleep(wait)
            try:
                self.poll()
                len(self.plugins)  # Make sure jenkins is fully started
                return  # By this time jenkins is back online
            except (HTTPError, ConnectionError):
                msg = (
                    "Jenkins has not restarted yet!  (This is"
                    " try {0} of {1}, waited {2} seconds so far)"
                    "  Sleeping and trying again.."
                )
                msg = msg.format(count, max_count, count * wait)
                log.debug(msg)
            count += 1
        msg = (
            "Jenkins did not come back from safe restart! "
            "Waited %s seconds altogether.  This "
            "failure may cause other failures."
        )
        log.critical(msg, count * wait)

    def __jenkins_is_unavailable(self):
        while True:
            try:
                res = self.requester.get_and_confirm_status(
                    self.baseurl, valid=[503, 500, 200]
                )
                # If there is a running job in Jenkins, the system message will
                # pop up but the Jenkins instance will return 200
                if (
                    res.status_code == 200
                    and "Jenkins is going to shut down"
                    in str(res.content, encoding="utf-8")
                ):
                    time.sleep(1)
                    continue
                return True
            except ConnectionError:
                # This is also a possibility while Jenkins is restarting
                return True
            except HTTPError:
                # This is a return code that is not 503,
                # so Jenkins is likely available
                time.sleep(1)

    def safe_exit(self, wait_for_exit: bool = True, max_wait: int = 360):
        """
        Restarts jenkins when no jobs are running, except for pipeline jobs
        """
        # NB: unlike other methods, the value of resp.status_code
        # here can be 503 even when everything is normal
        url = f"{self.baseurl}/safeExit"
        valid = self.requester.VALID_STATUS_CODES + [503, 500]
        resp = self.requester.post_and_confirm_status(
            url, data="", valid=valid
        )
        if wait_for_exit:
            self._wait_for_exit(max_wait=max_wait)
        return resp

    def _wait_for_exit(self, max_wait: int = 360) -> None:
        # We need to make sure all non pipeline jobs have finished,
        # and that jenkins is unavailable
        self.__jenkins_is_unresponsive(max_wait=max_wait)

    def __jenkins_is_unresponsive(self, max_wait: int = 360):
        # Blocks until jenkins returns ConnectionError or JenkinsAPIException
        # Default wait is one hour
        is_alive = True
        wait = 0
        while is_alive and wait < max_wait:
            try:
                self.requester.get_and_confirm_status(
                    self.baseurl, valid=[200]
                )
                time.sleep(1)
                wait += 1
                is_alive = True
            except (ConnectionError, JenkinsAPIException):
                # Jenkins is finally down
                is_alive = False
                return True
            except HTTPError:
                # This is a return code that is not 503,
                # so Jenkins is likely available, and we need to wait
                time.sleep(1)
                wait += 1
                is_alive = True

    def quiet_down(self):
        """
        Put Jenkins in a Quiet mode, preparation for restart.
        No new builds started
        """
        # NB: unlike other methods, the value of resp.status_code
        # here can be 503 even when everything is normal
        url = "%s/quietDown" % (self.baseurl,)
        valid = self.requester.VALID_STATUS_CODES + [503, 500]
        resp = self.requester.post_and_confirm_status(
            url, data="", valid=valid
        )
        return resp

    def cancel_quiet_down(self):
        """Cancel the effect of the quiet-down command"""
        # NB: unlike other methods, the value of resp.status_code
        # here can be 503 even when everything is normal
        url = "%s/cancelQuietDown" % (self.baseurl,)
        valid = self.requester.VALID_STATUS_CODES + [503, 500]
        resp = self.requester.post_and_confirm_status(
            url, data="", valid=valid
        )
        return resp

    @property
    def plugins(self):
        return self.get_plugins()

    def get_plugins(self, depth: int = 1) -> Plugins:
        url = self.get_plugins_url(depth=depth)
        return Plugins(url, self)

    def has_plugin(self, plugin_name: str) -> bool:
        return plugin_name in self.plugins

    def get_executors(self, nodename: str) -> Executors:
        url = f"{self.baseurl}/computer/{nodename}"
        return Executors(url, nodename, self)

    def get_master_data(self):
        url = f"{self.baseurl}/computer/api/python"
        return self.get_data(url)

    @property
    def version(self) -> str:
        """
        Return version number of Jenkins
        """
        response = self.requester.get_and_confirm_status(self.baseurl)
        version_key = "X-Jenkins"
        return response.headers.get(version_key, "0.0")

    def get_credentials(self, cred_class=Credentials2x):
        """
        Return credentials
        """

        if "credentials" not in self.plugins:
            raise JenkinsAPIException("Credentials plugin not installed")

        if self.plugins["credentials"].version.startswith("1."):
            url = f"{self.baseurl}/credential-store/domain/_/"
            return Credentials(url, self)

        url = f"{self.baseurl}/credentials/store/system/domain/_/"
        return cred_class(url, self)

    @property
    def credentials(self):
        return self.get_credentials(Credentials2x)

    @property
    def credentials_by_id(self):
        return self.get_credentials(CredentialsById)

    @property
    def is_quieting_down(self) -> bool:
        url = "%s/api/python?tree=quietingDown" % (self.baseurl,)
        data = self.get_data(url=url)
        return data.get("quietingDown", False)

    def shutdown(self) -> None:
        url = "%s/exit" % self.baseurl
        self.requester.post_and_confirm_status(url, data="")

    def generate_new_api_token(
        self, new_token_name: str = "Token By jenkinsapi python"
    ):
        subUrl = (
            "/me/descriptorByName/jenkins.security."
            "ApiTokenProperty/generateNewToken"
        )
        url = "%s%s" % (self.baseurl, subUrl)
        data = urlencode({"newTokenName": new_token_name})
        response = self.requester.post_and_confirm_status(url, data=data)
        token = response.json()["data"]["tokenValue"]
        return token

    def run_groovy_script(self, script: str) -> str:
        """
        Runs the requested groovy script on the Jenkins server returning the
        result as text.
        Raises a JenkinsAPIException if the returned HTTP response code from
        the POST request is not 200 OK.

        Example:

            server = Jenkins(...)
            script = 'println "Hello world!"'
            result = server.run_groovy_script(script)
            print(result) # will print "Hello world!"
        """
        url = f"{self.baseurl}/scriptText"
        data = urlencode({"script": script})

        response = self.requester.post_and_confirm_status(url, data=data)
        if response.status_code != 200:
            raise JenkinsAPIException(
                "Unexpected response %d." % response.status_code
            )

        return response.text

    def use_auth_cookie(self) -> None:
        assert self.username and self.baseurl, (
            "Please provide jenkins url, username "
            "and password to get the session ID cookie."
        )

        login_url = "j_acegi_security_check"
        jenkins_url = "{0}/{1}".format(self.baseurl, login_url)
        data = urlencode(
            {"j_username": self.username, "j_password": self.password}
        ).encode("utf-8")

        class SmartRedirectHandler(HTTPRedirectHandler):
            def extract_cookie(self, setcookie):
                # Extracts the last cookie.
                # Example of set-cookie value for python2
                # ('set-cookie', 'JSESSIONID.30blah=blahblahblah;Path=/;
                #   HttpOnly, JSESSIONID.30ablah=blahblah;Path=/;HttpOnly'),
                return setcookie.split(",")[-1].split(";")[0].strip("\n\r ")

            def http_error_302(self, req, fp, code, msg, headers):
                # Jenkins can send several Set-Cookie values sometimes
                #  The valid one is the last one
                for header, value in headers.items():
                    if header.lower() == "set-cookie":
                        cookie = self.extract_cookie(value)

                req.headers["Cookie"] = cookie
                result = HTTPRedirectHandler.http_error_302(
                    self, req, fp, code, msg, headers
                )
                result.orig_status = code
                result.orig_headers = headers
                result.cookie = cookie
                return result

        request = Request(jenkins_url, data)
        opener = build_opener(SmartRedirectHandler())
        res = opener.open(request)
        Requester.AUTH_COOKIE = res.cookie
