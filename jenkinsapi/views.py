"""
Module for jenkinsapi Views
"""

import logging
import json
from jenkinsapi.view import View
from jenkinsapi.custom_exceptions import JenkinsAPIException

log = logging.getLogger(__name__)


class Views(object):
    """
    An abstraction on a Jenkins object's views
    """

    LIST_VIEW = "hudson.model.ListView"
    NESTED_VIEW = "hudson.plugins.nested_view.NestedView"
    CATEGORIZED_VIEW = (
        "org.jenkinsci.plugins.categorizedview.CategorizedJobsView"
    )
    MY_VIEW = "hudson.model.MyView"
    DASHBOARD_VIEW = "hudson.plugins.view.dashboard.Dashboard"
    PIPELINE_VIEW = (
        "au.com.centrumsystems.hudson."
        "plugin.buildpipeline.BuildPipelineView"
    )

    def __init__(self, jenkins):
        self.jenkins = jenkins
        self._data = None

    def poll(self, tree=None):
        self._data = self.jenkins.poll(
            tree="views[name,url]" if tree is None else tree
        )

    def __len__(self):
        return len(self.keys())

    def __delitem__(self, view_name):
        if view_name == "All":
            raise ValueError("Cannot delete this view: %s" % view_name)

        if view_name in self:
            self[view_name].delete()
            self.poll()

    def __setitem__(self, view_name, job_names_list):
        new_view = self.create(view_name)
        if isinstance(job_names_list, str):
            job_names_list = [job_names_list]
        for job_name in job_names_list:
            if not new_view.add_job(job_name):
                # Something wrong - delete view
                del self[new_view]
                raise TypeError("Job %s does not exist in Jenkins" % job_name)

    def __getitem__(self, view_name):
        self.poll()
        for row in self._data.get("views", []):
            if row["name"] == view_name:
                return View(row["url"], row["name"], self.jenkins)

        raise KeyError("View %s not found" % view_name)

    def iteritems(self):
        """
        Get the names & objects for all views
        """
        self.poll()
        for row in self._data.get("views", []):
            name = row["name"]
            url = row["url"]

            yield name, View(url, name, self.jenkins)

    def __contains__(self, view_name):
        """
        True if view_name is the name of a defined view
        """
        return view_name in self.keys()

    def iterkeys(self):
        """
        Get the names of all available views
        """
        self.poll()
        for row in self._data.get("views", []):
            yield row["name"]

    def keys(self):
        """
        Return a list of the names of all views
        """
        return list(self.iterkeys())

    def create(self, view_name, view_type=LIST_VIEW, config=None):
        """
        Create a view
        :param view_name: name of new view, str
        :param view_type: type of the view, one of the constants in Views, str
        :param config: XML configuration of the new view
        :return: new View obj or None if view was not created
        """
        log.info('Creating "%s" view "%s"', view_type, view_name)

        if view_name in self:
            log.warning('View "%s" already exists', view_name)
            return self[view_name]

        url = "%s/createView" % self.jenkins.baseurl

        if view_type == self.CATEGORIZED_VIEW:
            if not config:
                raise JenkinsAPIException(
                    "Job XML config cannot be empty for CATEGORIZED_VIEW"
                )

            params = {"name": view_name}

            self.jenkins.requester.post_xml_and_confirm_status(
                url, data=config, params=params
            )
        else:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "name": view_name,
                "mode": view_type,
                "Submit": "OK",
                "json": json.dumps({"name": view_name, "mode": view_type}),
            }

            self.jenkins.requester.post_and_confirm_status(
                url, data=data, headers=headers
            )

        self.poll()
        return self[view_name]
