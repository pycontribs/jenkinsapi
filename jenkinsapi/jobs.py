"""
This module implements the Jobs class, which is intended to be a container-like
interface for all of the jobs defined on a single Jenkins server.
"""

from __future__ import annotations

from typing import Iterator
import logging
import time
from urllib.parse import quote, unquote

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
        normalized_name = self._normalize_job_name(job_name)
        if normalized_name in self:
            try:
                delete_job_url = self[normalized_name].get_delete_url()
                self.jenkins.requester.post_and_confirm_status(
                    delete_job_url, data="some random bytes..."
                )

                self._del_data(normalized_name)
            except JenkinsAPIException:
                # Sometimes jenkins throws NPE when removing job
                # It removes job ok, but it is good to be sure
                # so we re-try if job was not deleted
                if normalized_name in self:
                    delete_job_url = self[normalized_name].get_delete_url()
                    self.jenkins.requester.post_and_confirm_status(
                        delete_job_url, data="some random bytes..."
                    )
                    self._del_data(normalized_name)

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
        normalized_name = self._normalize_job_name(job_name)
        if normalized_name in self:
            job_data = next(
                job_row
                for job_row in self._data
                if self._job_row_matches_name(job_row, normalized_name)
            )
            name = self._normalize_job_name(job_data["name"])
            if name != normalized_name:
                name = normalized_name
            return Job(
                Job.strip_trailing_slash(job_data["url"]),
                name,
                self.jenkins,
            )
        else:
            raise UnknownJob(normalized_name)

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
        normalized_name = self._normalize_job_name(job_name)
        if not self._data:
            self._data = self.poll().get("jobs", [])
        return any(
            self._job_row_matches_name(job_row, normalized_name)
            for job_row in self._data
        )

    def iterkeys(self) -> Iterator[str]:
        """
        Iterate over the names of all available jobs
        """
        if not self._data:
            self._data = self.poll().get("jobs", [])
        for row in self._data:
            row_name = self._normalize_job_name(row["name"])
            full_name = self._get_full_name_from_row(row)
            if "/" in full_name:
                yield full_name
            elif row_name:
                yield row_name
            else:
                yield full_name

    def itervalues(self) -> Iterator["Job"]:
        """
        Iterate over all available jobs
        """
        if not self._data:
            self._data = self.poll().get("jobs", [])
        for row in self._data:
            yield Job(
                Job.strip_trailing_slash(row["url"]),
                row["name"],
                self.jenkins,
            )

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
        full_name, folder_parts, job_leaf = self._split_job_name(job_name)
        if full_name in self:
            return self[full_name]

        if not config:
            raise JenkinsAPIException("Job XML config cannot be empty")

        create_url = self._get_create_url(folder_parts)
        params = {"name": job_leaf}
        if isinstance(config, bytes):
            config = config.decode("utf-8")

        self.jenkins.requester.post_xml_and_confirm_status(
            create_url, data=config, params=params
        )
        # Reset to get it refreshed from Jenkins
        self._data = []

        return Job(self._build_job_url(full_name), full_name, self.jenkins)

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

        full_name, folder_parts, job_leaf = self._split_job_name(job_name)
        params = {"name": job_leaf}
        if isinstance(config, bytes):
            config = config.decode("utf-8")

        self.jenkins.requester.post_xml_and_confirm_status(
            self._get_create_url(folder_parts), data=config, params=params
        )
        # Reset to get it refreshed from Jenkins
        self._data = []

        # Launch a first scan / indexing to discover the branches...
        self.jenkins.requester.post_and_confirm_status(
            "{}/build".format(self._build_job_url(full_name)),
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
                "{}/indexing/consoleText".format(
                    self._build_job_url(full_name)
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
            if name.startswith(full_name + "/"):
                jobs.append(self[name])

        return jobs

    def copy(self, job_name: str, new_job_name: str) -> "Job":
        """
        Copy a job
        :param str job_name: Name of an existing job
        :param new_job_name: Name of new job
        :returns Job: new Job object
        """
        full_source_name = self._normalize_job_name(job_name)
        full_target_name, folder_parts, job_leaf = self._split_job_name(
            new_job_name
        )
        params = {"name": job_leaf, "mode": "copy", "from": full_source_name}

        self.jenkins.requester.post_and_confirm_status(
            self._get_create_url(folder_parts), params=params, data=""
        )

        self._data = []

        return self[full_target_name]

    @staticmethod
    def _normalize_job_name(job_name: str) -> str:
        name = (job_name or "").strip().strip("/")
        if not name:
            return name
        if name.startswith("job/"):
            name = name[4:]
        if "/job/" in name:
            name = name.replace("/job/", "/").lstrip("/")
        return name

    def _split_job_name(self, job_name: str) -> tuple[str, list[str], str]:
        full_name = self._normalize_job_name(job_name)
        parts = [part for part in full_name.split("/") if part]
        if not parts:
            return full_name, [], ""
        return full_name, parts[:-1], parts[-1]

    def _get_full_name_from_row(self, row: dict) -> str:
        url = row.get("url", "")
        path = url.replace(self.jenkins.baseurl, "").strip("/")
        if path:
            tokens = path.split("/")
            parts = []
            idx = 0
            while idx < len(tokens):
                if tokens[idx] == "job" and idx + 1 < len(tokens):
                    parts.append(unquote(tokens[idx + 1]))
                    idx += 2
                else:
                    idx += 1
            if parts:
                return "/".join(parts)
        return self._normalize_job_name(
            Job.get_full_name_from_url_and_baseurl(url, self.jenkins.baseurl)
        )

    def _job_row_matches_name(self, row: dict, normalized_name: str) -> bool:
        if self._normalize_job_name(row.get("name", "")) == normalized_name:
            return True
        return self._get_full_name_from_row(row) == normalized_name

    def _get_create_url(self, folder_parts: list[str]) -> str:
        if not folder_parts:
            return self.jenkins.get_create_url()
        folder_path = "/job/".join(quote(part) for part in folder_parts)
        return "{}/job/{}/createItem".format(self.jenkins.baseurl, folder_path)

    def _build_job_url(self, full_name: str) -> str:
        parts = [part for part in full_name.split("/") if part]
        if not parts:
            return self.jenkins.baseurl
        job_path = "/job/".join(quote(part) for part in parts)
        return "{}/job/{}".format(self.jenkins.baseurl, job_path)

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
