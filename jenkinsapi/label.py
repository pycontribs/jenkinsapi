"""
Module for jenkinsapi labels
"""

from jenkinsapi.jenkinsbase import JenkinsBase
import logging

log = logging.getLogger(__name__)


class Label(JenkinsBase):
    """
    Class to hold information on labels that tied to a collection of jobs
    """

    def __init__(self, baseurl, labelname, jenkins_obj):
        """
        Init a label object by providing all relevant pointers to it
        :param baseurl: basic url for querying information on a node
        :param labelname: name of the label
        :param jenkins_obj: ref to the jenkins obj
        :return: Label obj
        """
        self.labelname = labelname
        self.jenkins = jenkins_obj
        self.baseurl = baseurl
        JenkinsBase.__init__(self, baseurl)

    def __str__(self):
        return "%s" % (self.labelname)

    def get_jenkins_obj(self):
        return self.jenkins

    def is_online(self):
        return not self.poll(tree="offline")["offline"]

    def get_tied_jobs(self):
        """
        Get a list of jobs.
        """
        if self.get_tied_job_names():
            for job in self.get_tied_job_names():
                yield self.get_jenkins_obj().get_job(job["name"])

    def get_tied_job_names(self):
        """
        Get a list of the name of tied jobs.
        """
        return self.poll(tree="tiedJobs[name]")["tiedJobs"]
