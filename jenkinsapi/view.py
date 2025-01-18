"""
Module for jenkinsapi views
"""

from __future__ import annotations

from typing import Iterator, Tuple

import logging

from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.job import Job
from jenkinsapi.custom_exceptions import NotFound


log: logging.Logger = logging.getLogger(__name__)


class View(JenkinsBase):
    """
    View class
    """

    def __init__(self, url: str, name: str, jenkins_obj: "Jenkins") -> None:
        self.name: str = name
        self.jenkins_obj: "Jenkins" = jenkins_obj
        JenkinsBase.__init__(self, url)
        self.deleted: bool = False

    def __len__(self) -> int:
        return len(self.get_job_dict().keys())

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def __getitem__(self, job_name) -> Job:
        assert isinstance(job_name, str)
        api_url = self.python_api_url(self.get_job_url(job_name))
        return Job(api_url, job_name, self.jenkins_obj)

    def __contains__(self, job_name: str) -> bool:
        """
        True if view_name is the name of a defined view
        """
        return job_name in self.keys()

    def delete(self) -> None:
        """
        Remove this view object
        """
        url: str = f"{self.baseurl}/doDelete"
        self.jenkins_obj.requester.post_and_confirm_status(url, data="")
        self.jenkins_obj.poll()
        self.deleted = True

    def keys(self) -> list[str]:
        return self.get_job_dict().keys()

    def iteritems(self) -> Iterator[Tuple[str, Job]]:
        it = self.get_job_dict().items()

        for name, url in it:
            yield name, Job(url, name, self.jenkins_obj)

    def values(self) -> list[Job]:
        return [a[1] for a in self.iteritems()]

    def items(self):
        return [a for a in self.iteritems()]

    def _get_jobs(self) -> Iterator[Tuple[str, str]]:
        if "jobs" in self._data:
            for viewdict in self._data["jobs"]:
                yield viewdict["name"], viewdict["url"]

    def get_job_dict(self) -> dict:
        return dict(self._get_jobs())

    def get_job_url(self, str_job_name: str) -> str:
        if str_job_name in self:
            return self.get_job_dict()[str_job_name]
        else:
            # noinspection PyUnboundLocalVariable
            views_jobs = ", ".join(self.get_job_dict().keys())
            raise NotFound(
                "Job %s is not known, available jobs"
                " in view are: %s" % (str_job_name, views_jobs)
            )

    def get_jenkins_obj(self) -> "Jenkins":
        return self.jenkins_obj

    def add_job(self, job_name: str, job=None) -> bool:
        """
        Add job to a view

        :param job_name: name of the job to be added
        :param job: Job object to be added
        :return: True if job has been added, False if job already exists or
         job not known to Jenkins
        """
        if not job:
            if job_name in self.get_job_dict():
                log.warning(
                    "Job %s is already in the view %s", job_name, self.name
                )
                return False
            else:
                # Since this call can be made from nested view,
                # which doesn't have any jobs, we can miss existing job
                # Thus let's create top level Jenkins and ask him
                # http://jenkins:8080/view/CRT/view/CRT-FB/view/CRT-SCRT-1301/
                top_jenkins = self.get_jenkins_obj().get_jenkins_obj_from_url(
                    self.baseurl.split("view/")[0]
                )
                if not top_jenkins.has_job(job_name):
                    log.error(
                        msg='Job "%s" is not known to Jenkins' % job_name
                    )
                    return False
                else:
                    job = top_jenkins.get_job(job_name)

        log.info(msg="Creating job %s in view %s" % (job_name, self.name))

        url = "%s/addJobToView" % self.baseurl
        params = {"name": job_name}

        self.get_jenkins_obj().requester.post_and_confirm_status(
            url, data={}, params=params
        )
        self.poll()
        log.debug(
            msg='Job "%s" has been added to a view "%s"'
            % (job.name, self.name)
        )
        return True

    def remove_job(self, job_name: str) -> bool:
        """
        Remove job from a view

        :param job_name: name of the job to be removed
        :return: True if job has been removed,
            False if job not assigned to this view
        """
        if job_name not in self:
            return False

        url = "%s/removeJobFromView" % self.baseurl
        params = {"name": job_name}

        self.get_jenkins_obj().requester.post_and_confirm_status(
            url, data={}, params=params
        )
        self.poll()
        log.debug(
            msg='Job "%s" has been added to a view "%s"'
            % (job_name, self.name)
        )
        return True

    def _get_nested_views(self) -> Iterator[Tuple[str, str]]:
        for viewdict in self._data.get("views", []):
            yield viewdict["name"], viewdict["url"]

    def get_nested_view_dict(self) -> dict:
        return dict(self._get_nested_views())

    def get_config_xml_url(self) -> str:
        return "%s/config.xml" % self.baseurl

    def get_config(self) -> str:
        """
        Return the config.xml from the view
        """
        url = self.get_config_xml_url()
        response = self.get_jenkins_obj().requester.get_and_confirm_status(url)
        return response.text

    def update_config(self, config: str) -> str:
        """
        Update the config.xml to the view
        """
        url = self.get_config_xml_url()
        config = str(config)  # cast unicode in case of Python 2

        response = self.get_jenkins_obj().requester.post_url(
            url, params={}, data=config
        )
        return response.text

    @property
    def views(self):
        return (
            self.get_jenkins_obj().get_jenkins_obj_from_url(self.baseurl).views
        )
