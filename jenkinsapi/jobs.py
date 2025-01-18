"""
This module implements the Jobs class, which is intended to be a container-like
interface for all of the jobs defined on a single Jenkins server.
"""

from __future__ import annotations

from typing import Iterator
import logging
import time

from jenkinsapi.job import Job
from jenkinsapi.custom_exceptions import JenkinsAPIException, UnknownJob

log = logging.getLogger(__name__)


class Jobs(object):
    """
    This class provides a container-like API which gives
    access to all jobs defined on the Jenkins server. It behaves
    like a dict in which keys are Job-names and values are actual
    jenkinsapi.Job objects.
    """

    def __init__(self, jenkins: "Jenkins") -> None:
        self.jenkins = jenkins
        self._data = []

    def _del_data(self, job_name: str) -> None:
        if not self._data:
            return
        for num, job_data in enumerate(self._data):
            if job_data["name"] == job_name:
                del self._data[num]
                return

    def __len__(self) -> int:
        return len(self.keys())

    def poll(self, tree="jobs[name,color,url]"):
        return self.jenkins.poll(tree=tree)

    def __delitem__(self, job_name: str) -> None:
        """
        Delete a job by name
        :param str job_name: name of a existing job
        :raises JenkinsAPIException:  When job is not deleted
        """
        if job_name in self:
            try:
                delete_job_url = self[job_name].get_delete_url()
                self.jenkins.requester.post_and_confirm_status(
                    delete_job_url, data="some random bytes..."
                )

                self._del_data(job_name)
            except JenkinsAPIException:
                # Sometimes jenkins throws NPE when removing job
                # It removes job ok, but it is good to be sure
                # so we re-try if job was not deleted
                if job_name in self:
                    delete_job_url = self[job_name].get_delete_url()
                    self.jenkins.requester.post_and_confirm_status(
                        delete_job_url, data="some random bytes..."
                    )
                    self._del_data(job_name)

    def __setitem__(self, key: str, value: str) -> "Job":
        """
        Create Job

        :param str key:     Job name
        :param str value:   XML configuration of the job

        .. code-block:: python
        api = Jenkins('http://localhost:8080/')
        new_job = api.jobs['my_new_job'] = config_xml
        """
        return self.create(key, value)

    def __getitem__(self, job_name: str) -> "Job":
        if job_name in self:
            job_data = [
                job_row
                for job_row in self._data
                if job_row["name"] == job_name
                or Job.get_full_name_from_url_and_baseurl(
                    job_row["url"], self.jenkins.baseurl
                )
                == job_name
            ][0]
            return Job(job_data["url"], job_data["name"], self.jenkins)
        else:
            raise UnknownJob(job_name)

    def iteritems(self) -> Iterator[str, "Job"]:
        """
        Iterate over the names & objects for all jobs
        """
        for job in self.itervalues():
            if job.name != job.get_full_name():
                yield job.get_full_name(), job
            else:
                yield job.name, job

    def __contains__(self, job_name: str) -> bool:
        """
        True if job_name exists in Jenkins
        """
        return job_name in self.keys()

    def iterkeys(self) -> Iterator[str]:
        """
        Iterate over the names of all available jobs
        """
        if not self._data:
            self._data = self.poll().get("jobs", [])
        for row in self._data:
            if row["name"] != Job.get_full_name_from_url_and_baseurl(
                row["url"], self.jenkins.baseurl
            ):
                yield Job.get_full_name_from_url_and_baseurl(
                    row["url"], self.jenkins.baseurl
                )
            else:
                yield row["name"]

    def itervalues(self) -> Iterator["Job"]:
        """
        Iterate over all available jobs
        """
        if not self._data:
            self._data = self.poll().get("jobs", [])
        for row in self._data:
            yield Job(row["url"], row["name"], self.jenkins)

    def keys(self) -> list[str]:
        """
        Return a list of the names of all jobs
        """
        return list(self.iterkeys())

    def create(self, job_name: str, config: str | bytes) -> "Job":
        """
        Create a job

        :param str jobname: Name of new job
        :param str config: XML configuration of new job
        :returns Job: new Job object
        """
        if job_name in self:
            return self[job_name]

        if not config:
            raise JenkinsAPIException("Job XML config cannot be empty")

        params = {"name": job_name}
        if isinstance(config, bytes):
            config = config.decode("utf-8")

        self.jenkins.requester.post_xml_and_confirm_status(
            self.jenkins.get_create_url(), data=config, params=params
        )
        # Reset to get it refreshed from Jenkins
        self._data = []

        return self[job_name]

    def create_multibranch_pipeline(
        self, job_name: str, config: str, block: bool = True, delay: int = 60
    ) -> list["Job"]:
        """
        Create a multibranch pipeline job

        :param str jobname: Name of new job
        :param str config: XML configuration of new job
        :param block: block until scan is finished?
        :param delay: max delay to wait for scan to finish (seconds)
        :returns list of new Jobs after scan
        """
        if not config:
            raise JenkinsAPIException("Job XML config cannot be empty")

        params = {"name": job_name}
        if isinstance(config, bytes):
            config = config.decode("utf-8")

        self.jenkins.requester.post_xml_and_confirm_status(
            self.jenkins.get_create_url(), data=config, params=params
        )
        # Reset to get it refreshed from Jenkins
        self._data = []

        # Launch a first scan / indexing to discover the branches...
        self.jenkins.requester.post_and_confirm_status(
            "{}/job/{}/build".format(self.jenkins.baseurl, job_name),
            data="",
            valid=[200, 302],  # expect 302 without redirects
            allow_redirects=False,
        )

        start_time = time.time()
        # redirect-url does not work with indexing;
        # so the only workaround found is to parse the console output
        # until scan has finished.
        scan_finished = False
        while not scan_finished and block and time.time() < start_time + delay:
            indexing_console_text = self.jenkins.requester.get_url(
                "{}/job/{}/indexing/consoleText".format(
                    self.jenkins.baseurl, job_name
                )
            )
            if (
                indexing_console_text.text.strip()
                .split("\n")[-1]
                .startswith("Finished:")
            ):
                scan_finished = True
            time.sleep(1)

        # now search for all jobs created; those who start with job_name + '/'
        jobs = []
        for name in self.jenkins.get_jobs_list():
            if name.startswith(job_name + "/"):
                jobs.append(self[name])

        return jobs

    def copy(self, job_name: str, new_job_name: str) -> "Job":
        """
        Copy a job
        :param str job_name: Name of an existing job
        :param new_job_name: Name of new job
        :returns Job: new Job object
        """
        params = {"name": new_job_name, "mode": "copy", "from": job_name}

        self.jenkins.requester.post_and_confirm_status(
            self.jenkins.get_create_url(), params=params, data=""
        )

        self._data = []

        return self[new_job_name]

    def rename(self, job_name: str, new_job_name: str) -> "Job":
        """
        Rename a job

        :param str job_name: Name of an existing job
        :param str new_job_name: Name of new job
        :returns Job: new Job object
        """
        params = {"newName": new_job_name}
        rename_job_url = self[job_name].get_rename_url()
        self.jenkins.requester.post_and_confirm_status(
            rename_job_url, params=params, data=""
        )

        self._data = []

        return self[new_job_name]

    def build(self, job_name: str, params=None, **kwargs) -> "QueueItem":
        """
        Executes build of a job

        :param str job_name:    Job name
        :param dict params:     Job parameters
        :param kwargs:          Parameters for Job.invoke() function
        :returns QueueItem:     Object to track build progress
        """
        if params:
            assert isinstance(params, dict)
            return self[job_name].invoke(build_params=params, **kwargs)

        return self[job_name].invoke(**kwargs)
