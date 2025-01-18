"""
jenkinsapi plugins
"""

from __future__ import annotations

from typing import Generator
import logging
import time
import re
from io import BytesIO
from urllib.parse import urlencode
import json

import requests
from jenkinsapi.plugin import Plugin
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.custom_exceptions import UnknownPlugin
from jenkinsapi.custom_exceptions import JenkinsAPIException
from jenkinsapi.utils.jsonp_to_json import jsonp_to_json
from jenkinsapi.utils.manifest import Manifest, read_manifest


log: logging.Logger = logging.getLogger(__name__)


class Plugins(JenkinsBase):
    """
    Plugins class for jenkinsapi
    """

    def __init__(self, url: str, jenkins_obj: "Jenkins") -> None:
        self.jenkins_obj: "Jenkins" = jenkins_obj
        JenkinsBase.__init__(self, url)

    def get_jenkins_obj(self) -> "Jenkins":
        return self.jenkins_obj

    def check_updates_server(self) -> None:
        url: str = (
            f"{self.jenkins_obj.baseurl}/pluginManager/checkUpdatesServer"
        )
        self.jenkins_obj.requester.post_and_confirm_status(
            url, params={}, data={}
        )

    @property
    def update_center_dict(self):
        update_center = "https://updates.jenkins.io/update-center.json"
        jsonp = requests.get(update_center).content.decode("utf-8")
        return json.loads(jsonp_to_json(jsonp))

    def _poll(self, tree=None):
        return self.get_data(self.baseurl, tree=tree)

    def keys(self) -> list[str]:
        return self.get_plugins_dict().keys()

    __iter__ = keys

    def iteritems(self) -> Generator[str, "Plugin"]:
        return self._get_plugins()

    def values(self) -> list["Plugin"]:
        return [a[1] for a in self.iteritems()]

    def _get_plugins(self) -> Generator[str, "Plugin"]:
        if "plugins" in self._data:
            for p_dict in self._data["plugins"]:
                yield p_dict["shortName"], Plugin(p_dict)

    def get_plugins_dict(self) -> dict[str, "Plugin"]:
        return dict(self._get_plugins())

    def __len__(self) -> int:
        return len(self.get_plugins_dict().keys())

    def __getitem__(self, plugin_name: str) -> Plugin:
        try:
            return self.get_plugins_dict()[plugin_name]
        except KeyError:
            raise UnknownPlugin(plugin_name)

    def __setitem__(self, shortName, plugin: "Plugin") -> None:
        """
        Installs plugin in Jenkins.

        If plugin already exists - this method is going to uninstall the
        existing plugin and install the specified version if it is not
        already installed.

        :param shortName: Plugin ID
        :param plugin a Plugin object to be installed.
        """
        if self.plugin_version_already_installed(plugin):
            return
        if plugin.is_latest(self.update_center_dict):
            self._install_plugin_from_updatecenter(plugin)
        else:
            self._install_specific_version(plugin)
        self._wait_until_plugin_installed(plugin)

    def _install_plugin_from_updatecenter(self, plugin: "Plugin") -> None:
        """
        Latest versions of plugins can be installed from the update
        center (and don't need a restart.)
        """
        xml_str: str = plugin.get_attributes()
        url: str = (
            "%s/pluginManager/installNecessaryPlugins"
            % self.jenkins_obj.baseurl
        )
        self.jenkins_obj.requester.post_xml_and_confirm_status(
            url, data=xml_str
        )

    @property
    def update_center_install_status(self):
        """
        Jenkins 2.x specific
        """
        url: str = "%s/updateCenter/installStatus" % self.jenkins_obj.baseurl
        status = self.jenkins_obj.requester.get_url(url)
        if status.status_code == 404:
            raise JenkinsAPIException(
                "update_center_install_status not available for Jenkins 1.X"
            )
        return status.json()

    @property
    def restart_required(self):
        """
        Call after plugin installation to check if Jenkins requires a restart
        """
        try:
            jobs = self.update_center_install_status["data"]["jobs"]
        except JenkinsAPIException:
            return True  # Jenkins 1.X has no update_center
        return any([job for job in jobs if job["requiresRestart"] == "true"])

    def _install_specific_version(self, plugin: "Plugin") -> None:
        """
        Plugins that are not the latest version have to be uploaded.
        """
        download_link: str = plugin.get_download_link(
            update_center_dict=self.update_center_dict
        )
        downloaded_plugin: BytesIO = self._download_plugin(download_link)
        plugin_dependencies = self._get_plugin_dependencies(downloaded_plugin)
        log.debug("Installing dependencies for plugin '%s'", plugin.shortName)
        self.jenkins_obj.install_plugins(plugin_dependencies)
        url = "%s/pluginManager/uploadPlugin" % self.jenkins_obj.baseurl
        requester = self.jenkins_obj.requester
        downloaded_plugin.seek(0)
        requester.post_and_confirm_status(
            url,
            files={"file": ("plugin.hpi", downloaded_plugin)},
            data={},
            params={},
        )

    def _get_plugin_dependencies(
        self, downloaded_plugin: BytesIO
    ) -> list["Plugin"]:
        """
        Returns a list of all dependencies for a downloaded plugin
        """
        plugin_dependencies = []
        manifest: Manifest = read_manifest(downloaded_plugin)
        manifest_dependencies = manifest.main_section.get(
            "Plugin-Dependencies"
        )
        if manifest_dependencies:
            dependencies = manifest_dependencies.split(",")
            for dep in dependencies:
                # split plugin:version;resolution:optional entries
                components = dep.split(";")
                dep_plugin = components[0]
                name = dep_plugin.split(":")[0]
                # install latest dependency, avoids multiple
                # versions of the same dep
                plugin_dependencies.append(
                    Plugin({"shortName": name, "version": "latest"})
                )
        return plugin_dependencies

    def _download_plugin(self, download_link):
        downloaded_plugin = BytesIO()
        downloaded_plugin.write(requests.get(download_link).content)
        return downloaded_plugin

    def _plugin_has_finished_installation(self, plugin) -> bool:
        """
        Return True if installation is marked as 'Success' or
        'SuccessButRequiresRestart' in Jenkins' update_center,
        else return False.
        """
        try:
            jobs = self.update_center_install_status["data"]["jobs"]
            for job in jobs:
                if job["name"] == plugin.shortName and job[
                    "installStatus"
                ] in [
                    "Success",
                    "SuccessButRequiresRestart",
                ]:
                    return True
            return False
        except JenkinsAPIException:
            return False  # lack of update_center in Jenkins 1.X

    def plugin_version_is_being_installed(self, plugin) -> bool:
        """
        Return true if plugin is currently being installed.
        """
        try:
            jobs = self.update_center_install_status["data"]["jobs"]
        except JenkinsAPIException:
            return False  # lack of update_center in Jenkins 1.X
        return any(
            [
                job
                for job in jobs
                if job["name"] == plugin.shortName
                and job["version"] == plugin.version
            ]
        )

    def plugin_version_already_installed(self, plugin) -> bool:
        """
        Check if plugin version is already installed
        """
        if plugin.shortName not in self:
            if self.plugin_version_is_being_installed(plugin):
                return True
            return False
        installed_plugin = self[plugin.shortName]
        if plugin.version == installed_plugin.version:
            return True
        elif plugin.version == "latest":
            # we don't have an exact version, we first check if Jenkins
            # knows about an update
            if (
                hasattr(installed_plugin, "hasUpdates")
                and installed_plugin.hasUpdates
            ):
                return False

            # Jenkins may not have an up-to-date catalogue,
            # so check update-center directly
            latest_version = self.update_center_dict["plugins"][
                plugin.shortName
            ]["version"]
            return installed_plugin.version == latest_version

        return False

    def __delitem__(self, shortName):
        if re.match(".*@.*", shortName):
            real_shortName = re.compile("(.*)@(.*)").search(shortName).group(1)
            raise ValueError(
                ("Plugin shortName can't contain version. '%s' should be '%s'")
                % (shortName, real_shortName)
            )
        if shortName not in self:
            raise KeyError(
                'Plugin with ID "%s" not found, cannot uninstall' % shortName
            )
        if self[shortName].deleted:
            raise JenkinsAPIException(
                'Plugin "%s" already marked for uninstall. '
                "Restart jenkins for uninstall to complete."
            )
        params = {"Submit": "OK", "json": {}}
        url = "%s/pluginManager/plugin/%s/doUninstall" % (
            self.jenkins_obj.baseurl,
            shortName,
        )
        self.jenkins_obj.requester.post_and_confirm_status(
            url, params={}, data=urlencode(params)
        )

        self.poll()
        if not self[shortName].deleted:
            raise JenkinsAPIException(
                "Problem uninstalling plugin '%s'." % shortName
            )

    def _wait_until_plugin_installed(self, plugin, maxwait=120, interval=1):
        for _ in range(maxwait, 0, -interval):
            self.poll()
            if self._plugin_has_finished_installation(plugin):
                return True
            if plugin.shortName in self:
                return True  # for Jenkins 1.X
            time.sleep(interval)

        if self.jenkins_obj.version.startswith("2"):
            raise JenkinsAPIException(
                "Problem installing plugin '%s'." % plugin.shortName
            )

        log.warning(
            "Plugin '%s' not found in loaded plugins."
            "You may need to restart Jenkins.",
            plugin.shortName,
        )
        return False

    def __contains__(self, plugin_name):
        """
        True if plugin_name is the name of a defined plugin
        """
        return plugin_name in self.keys()

    def __str__(self):
        plugins = [
            plugin["shortName"] for plugin in self._data.get("plugins", [])
        ]
        return str(sorted(plugins))
