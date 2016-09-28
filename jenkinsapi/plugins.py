"""
jenkinsapi plugins
"""
from __future__ import print_function

import logging
import time
import zipfile
try:
    from StringIO import StringIO
    from urllib import urlencode
except ImportError:
    # Python3
    from io import BytesIO as StringIO
    from urllib.parse import urlencode
import json
import requests
from jenkinsapi.plugin import Plugin
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.custom_exceptions import UnknownPlugin
from jenkinsapi.custom_exceptions import JenkinsAPIException
from jenkinsapi.utils.jsonp_to_json import jsonp_to_json


log = logging.getLogger(__name__)


class Plugins(JenkinsBase):

    """
    Plugins class for jenkinsapi
    """

    def __init__(self, url, jenkins_obj):
        self.jenkins_obj = jenkins_obj
        JenkinsBase.__init__(self, url)
        # print('DEBUG: Plugins._data=', self._data)

    def get_jenkins_obj(self):
        return self.jenkins_obj

    def check_updates_server(self):
        url = (
            '%s/pluginManager/checkUpdatesServer'
            % self.jenkins_obj.baseurl
        )
        self.jenkins_obj.requester.post_and_confirm_status(url, params={}, data={})

    @property
    def update_center_dict(self):
        update_center = 'https://updates.jenkins-ci.org/update-center.json'
        jsonp = requests.get(update_center).content.decode('utf-8')
        return json.loads(jsonp_to_json(jsonp))

    def _poll(self, tree=None):
        return self.get_data(self.baseurl, tree=tree)

    def keys(self):
        return self.get_plugins_dict().keys()

    __iter__ = keys

    def iteritems(self):
        return self._get_plugins()

    def values(self):
        return [a[1] for a in self.iteritems()]

    def _get_plugins(self):
        if 'plugins' in self._data:
            for p_dict in self._data["plugins"]:
                yield p_dict["shortName"], Plugin(p_dict)

    def get_plugins_dict(self):
        return dict(self._get_plugins())

    def __len__(self):
        return len(self.get_plugins_dict().keys())

    def __getitem__(self, plugin_name):
        try:
            return self.get_plugins_dict()[plugin_name]
        except KeyError:
            raise UnknownPlugin(plugin_name)

    def __setitem__(self, shortName, plugin):
        """
        Installs plugin in Jenkins.

        If plugin already exists - this method is going to uninstall the existing
        plugin and install the specified version if it is not already installed.

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

    def _install_plugin_from_updatecenter(self, plugin):
        """
        Latest versions of plugins can be installed from the update center (and don't need a restart.)
        """
        xml_str = plugin.get_attributes()
        url = (
            '%s/pluginManager/installNecessaryPlugins' % self.jenkins_obj.baseurl
        )
        self.jenkins_obj.requester.post_xml_and_confirm_status(url, data=xml_str)

    @property
    def update_center_install_status(self):
        """
        Jenkins 2.x specific
        """
        url = "%s/updateCenter/installStatus" % self.jenkins_obj.baseurl
        status = self.jenkins_obj.requester.get_url(url)
        return status.json()

    def _install_specific_version(self, plugin):
        """
        Plugins that are not the latest version have to be uploaded.
        """
        download_link = plugin.get_download_link(update_center_dict=self.update_center_dict)
        downloaded_plugin = self._download_plugin(download_link)
        plugin_dependencies = self._get_plugin_dependencies(downloaded_plugin)
        self.jenkins_obj.install_plugins(plugin_dependencies)
        url = ('%s/pluginManager/uploadPlugin' % self.jenkins_obj.baseurl)
        requester = self.jenkins_obj.requester
        downloaded_plugin.seek(0)
        requester.post_and_confirm_status(url, files={'file': ('plugin.hpi', downloaded_plugin)}, data={}, params={})

    def _get_plugin_dependencies(self, downloaded_plugin):
        """
        Returns a list of all dependencies for a downloaded plugin
        """
        plugin_dependencies = []
        for line in self.__get_manifest(downloaded_plugin):
            line = line.decode('UTF-8')
            if line.startswith('Plugin-Dependencies: '):
                dependencies = line.strip().split('Plugin-Dependencies: ')[1].split(',')
                for dep in dependencies:
                    components = dep.split(';')  # split plugin:version;resolution:optional entries
                    dep_plugin = components[0]
                    name = dep_plugin.split(':')[0]
                    # install latest dependency, avoids multiple versions of the same dep
                    plugin_dependencies.append(Plugin({'shortName': name, 'version': 'latest'}))
        return plugin_dependencies

    def _download_plugin(self, download_link):
        downloaded_plugin = StringIO()
        downloaded_plugin.write(requests.get(download_link).content)
        return downloaded_plugin

    def __get_manifest(self, downloaded_plugin):
        with zipfile.ZipFile(downloaded_plugin) as archive:
            return archive.open('META-INF/MANIFEST.MF')

    def _plugin_has_finished_installation(self, plugin):
        """
        Return True if installation is marked as 'Success' or 'SuccessButRequiresRestart'
        in Jenkins' update_center, else return False.
        """
        if self.jenkins_obj.version.startswith('1'):
            # We have no good way of knowing if a plugin has finished installing.
            # Most plugins install rapidly, so we return False and the calling method
            # checks if the plugin has been loaded or the maximum timespan has passed.
            return False
        else:
            jobs = self.update_center_install_status['data']['jobs']
            for job in jobs:
                if job['name'] == plugin.shortName and job['installStatus'] in ['Success', 'SuccessButRequiresRestart']:
                    return True
            return False

    def plugin_version_already_installed(self, plugin):
        """
        Check if plugin version is already installed
        """
        if plugin.shortName not in self:
            return False  # plugin not installed
        installed_plugin = self[plugin.shortName]
        if plugin.version == installed_plugin.version:
            return True
        elif plugin.version == "latest":
            # we don't have an exact version, we first check if Jenkins knows about an update
            if hasattr(installed_plugin, 'hasUpdates') and installed_plugin.hasUpdates:
                return False
            else:
                # Jenkins may not have an up-to-date catalogue, so check update-center directly
                latest_version = self.update_center_dict['plugins'][plugin.shortName]['version']
                return installed_plugin.version == latest_version
        else:
            return False

    def __delitem__(self, shortName):
        if shortName not in self:
            raise KeyError(
                'Plugin with ID "%s" not found, cannot uninstall' % shortName)
        if self[shortName].deleted:
            raise JenkinsAPIException('Plugin "%s" already marked for uninstall. '
                                      'Restart jenkins for uninstall to complete.')
        params = {
            'Submit': 'OK',
            'json': {}
        }
        url = ('%s/pluginManager/plugin/%s/doUninstall'
               % (self.jenkins_obj.baseurl, shortName))
        self.jenkins_obj.requester.post_and_confirm_status(
            url, params={}, data=urlencode(params)
        )

        self.poll()
        if not self[shortName].deleted:
            raise JenkinsAPIException("Problem uninstalling plugin '%s'." % shortName)

    def _wait_until_plugin_installed(self, plugin, maxwait=120, interval=1):
        for _ in range(maxwait, 0, -interval):
            self.poll()
            if self._plugin_has_finished_installation(plugin):
                return
            if plugin.shortName in self:
                return True  # for Jenkins 1.X
            time.sleep(interval)
        if self.jenkins_obj.version.startswith('2'):
            raise JenkinsAPIException("Problem installing plugin '%s'." % plugin.shortName)
        else:
            log.warning("Plugin '%s' not found in loaded plugins."
                        "You may need to restart Jenkins.", plugin.shortName)

    def __contains__(self, plugin_name):
        """
        True if plugin_name is the name of a defined plugin
        """
        return plugin_name in self.keys()

    def __str__(self):
        plugins = [plugin["shortName"]
                   for plugin in self._data.get("plugins", [])]
        return str(sorted(plugins))
