"""
jenkinsapi_tests.test_plugins
"""

import mock

# To run unittests on python 2.6 please use unittest2 library
try:
    import unittest2 as unittest
except ImportError:
    import unittest
try:
    from StringIO import StringIO  # python2
except ImportError:
    from io import BytesIO as StringIO  # python3
import zipfile

from jenkinsapi.jenkins import Requester
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.plugins import Plugins
from jenkinsapi.plugin import Plugin


class TestPlugins(unittest.TestCase):
    DATA = {
        "plugins": [
            {
                "deleted": False,
                "hasUpdate": True,
                "downgradable": False,
                "dependencies": [{}, {}, {}, {}],
                "longName": "Jenkins Subversion Plug-in",
                "active": True,
                "shortName": "subversion",
                "backupVersion": None,
                "url": "http://wiki.jenkins-ci.org/display/"
                "JENKINS/Subversion+Plugin",
                "enabled": True,
                "pinned": False,
                "version": "1.45",
                "supportsDynamicLoad": "MAYBE",
                "bundled": True,
            },
            {
                "deleted": False,
                "hasUpdate": True,
                "downgradable": False,
                "dependencies": [{}, {}],
                "longName": "Maven Integration plugin",
                "active": True,
                "shortName": "maven-plugin",
                "backupVersion": None,
                "url": "http://wiki.jenkins-ci.org/display/JENKINS/"
                "Maven+Project+Plugin",
                "enabled": True,
                "pinned": False,
                "version": "1.521",
                "supportsDynamicLoad": "MAYBE",
                "bundled": True,
            },
        ]
    }

    @mock.patch.object(Jenkins, "_poll")
    def setUp(self, _poll_jenkins):
        _poll_jenkins.return_value = {}

        self.J = Jenkins("http://localhost:8080")

    @mock.patch.object(Plugins, "_poll")
    def test_get_plugins(self, _poll_plugins):
        _poll_plugins.return_value = self.DATA

        # Can we produce a repr string for this object
        self.assertIsInstance(self.J.get_plugins(), Plugins)

    @mock.patch.object(Plugins, "_poll")
    def test_no_plugins_str(self, _poll_plugins):
        _poll_plugins.return_value = {}

        plugins = self.J.get_plugins()
        self.assertEqual(str(plugins), "[]")

    @mock.patch.object(Plugins, "_poll")
    def test_plugins_str(self, _poll_plugins):
        _poll_plugins.return_value = self.DATA

        plugins = self.J.get_plugins()
        self.assertEqual(str(plugins), "['maven-plugin', 'subversion']")

    @mock.patch.object(Plugins, "_poll")
    def test_plugins_len(self, _poll_plugins):
        _poll_plugins.return_value = self.DATA

        plugins = self.J.get_plugins()
        self.assertEqual(len(plugins), 2)

    @mock.patch.object(Plugins, "_poll")
    def test_plugins_contains(self, _poll_plugins):
        _poll_plugins.return_value = self.DATA

        plugins = self.J.get_plugins()
        self.assertIn("subversion", plugins)
        self.assertIn("maven-plugin", plugins)

    @mock.patch.object(Plugins, "_poll")
    def test_plugins_values(self, _poll_plugins):
        _poll_plugins.return_value = self.DATA

        p = Plugin(
            {
                "deleted": False,
                "hasUpdate": True,
                "downgradable": False,
                "dependencies": [{}, {}, {}, {}],
                "longName": "Jenkins Subversion Plug-in",
                "active": True,
                "shortName": "subversion",
                "backupVersion": None,
                "url": "http://wiki.jenkins-ci.org/display/JENKINS/"
                "Subversion+Plugin",
                "enabled": True,
                "pinned": False,
                "version": "1.45",
                "supportsDynamicLoad": "MAYBE",
                "bundled": True,
            }
        )

        plugins = self.J.get_plugins().values()
        self.assertIn(p, plugins)

    @mock.patch.object(Plugins, "_poll")
    def test_plugins_keys(self, _poll_plugins):
        _poll_plugins.return_value = self.DATA

        plugins = self.J.get_plugins().keys()
        self.assertIn("subversion", plugins)
        self.assertIn("maven-plugin", plugins)

    @mock.patch.object(Plugins, "_poll")
    def test_plugins_empty(self, _poll_plugins):
        _poll_plugins.return_value = {}

        # list() is required here for python 3.x compatibility
        plugins = list(self.J.get_plugins().keys())
        self.assertEqual([], plugins)

    @mock.patch.object(Plugins, "_poll")
    def test_plugin_get_by_name(self, _poll_plugins):
        _poll_plugins.return_value = self.DATA

        p = Plugin(
            {
                "deleted": False,
                "hasUpdate": True,
                "downgradable": False,
                "dependencies": [{}, {}, {}, {}],
                "longName": "Jenkins Subversion Plug-in",
                "active": True,
                "shortName": "subversion",
                "backupVersion": None,
                "url": "http://wiki.jenkins-ci.org/display/JENKINS/"
                "Subversion+Plugin",
                "enabled": True,
                "pinned": False,
                "version": "1.45",
                "supportsDynamicLoad": "MAYBE",
                "bundled": True,
            }
        )

        plugin = self.J.get_plugins()["subversion"]
        self.assertEqual(p, plugin)

    @mock.patch.object(Plugins, "_poll")
    def test_get_plugin_details(self, _poll_plugins):
        _poll_plugins.return_value = self.DATA
        plugin = self.J.get_plugins()["subversion"]
        self.assertEqual("1.45", plugin.version)
        self.assertEqual("subversion", plugin.shortName)
        self.assertEqual("Jenkins Subversion Plug-in", plugin.longName)
        self.assertEqual(
            "http://wiki.jenkins-ci.org/display/JENKINS/" "Subversion+Plugin",
            plugin.url,
        )

    @mock.patch.object(Requester, "post_xml_and_confirm_status")
    def test_install_plugin_bad_input(self, _post):
        with self.assertRaises(ValueError):
            self.J.install_plugin("test")

    @mock.patch.object(Requester, "post_xml_and_confirm_status")
    def test_delete_plugin_bad_input(self, _post):
        with self.assertRaises(ValueError):
            self.J.delete_plugin("test@latest")

    @mock.patch.object(Plugins, "update_center_dict")
    @mock.patch.object(Plugins, "_poll")
    @mock.patch.object(Plugins, "plugin_version_already_installed")
    @mock.patch.object(Plugins, "restart_required")
    @mock.patch.object(Plugins, "_wait_until_plugin_installed")
    @mock.patch.object(Requester, "post_xml_and_confirm_status")
    @mock.patch.object(Jenkins, "safe_restart")
    def test_install_plugin_good_input(
        self,
        _reboot,
        _post,
        _wait,
        _restart_required,
        already_installed,
        _poll_plugins,
        _center_dict,
    ):
        _poll_plugins.return_value = self.DATA
        already_installed.return_value = False
        self.J.install_plugin("test@latest")
        expected_data = '<jenkins> <install plugin="test@latest" /> </jenkins>'
        _post.assert_called_with(
            "/".join(
                [self.J.baseurl, "pluginManager", "installNecessaryPlugins"]
            ),
            data=expected_data,
        )

    @mock.patch.object(Plugins, "update_center_dict")
    @mock.patch.object(Plugins, "_poll")
    @mock.patch.object(Plugins, "plugin_version_already_installed")
    @mock.patch.object(
        Plugins, "restart_required", new_callable=mock.mock.PropertyMock
    )
    @mock.patch.object(Plugins, "_wait_until_plugin_installed")
    @mock.patch.object(Requester, "post_xml_and_confirm_status")
    @mock.patch.object(Jenkins, "safe_restart")
    def test_install_plugins_good_input_no_restart_required(
        self,
        _restart,
        _post,
        _wait,
        restart_required,
        already_installed,
        _poll_plugins,
        _center_dict,
    ):
        _poll_plugins.return_value = self.DATA
        restart_required.return_value = False
        already_installed.return_value = False
        self.J.install_plugins(["test@latest", "test@latest"])
        self.assertEqual(_post.call_count, 2)
        self.assertEqual(_restart.call_count, 0)

    @mock.patch.object(Plugins, "update_center_dict")
    @mock.patch.object(Plugins, "_poll")
    @mock.patch.object(Plugins, "plugin_version_already_installed")
    @mock.patch.object(
        Plugins, "restart_required", new_callable=mock.mock.PropertyMock
    )
    @mock.patch.object(Plugins, "_wait_until_plugin_installed")
    @mock.patch.object(Requester, "post_xml_and_confirm_status")
    @mock.patch.object(Jenkins, "safe_restart")
    def test_install_plugins_good_input_with_restart_required(
        self,
        _restart,
        _post,
        _wait,
        restart_required,
        already_installed,
        _poll_plugins,
        _center_dict,
    ):
        _poll_plugins.return_value = self.DATA
        restart_required.return_value = True
        already_installed.return_value = False
        self.J.install_plugins(["test@latest", "test@latest"])
        self.assertEqual(_post.call_count, 2)
        self.assertEqual(_restart.call_count, 1)

    @mock.patch.object(Plugins, "_poll")
    def test_get_plugin_dependencies(self, _poll_plugins):
        manifest = (
            "Manifest-Version: 1.0\n"
            "bla: somestuff\n"
            "Plugin-Dependencies: aws-java-sdk:1.10.45,aws-credentials:1.15"
        )
        downloaded_plugin = StringIO()
        zipfile.ZipFile(downloaded_plugin, mode="w").writestr(
            "META-INF/MANIFEST.MF", manifest
        )
        _poll_plugins.return_value = self.DATA
        dependencies = self.J.plugins._get_plugin_dependencies(
            downloaded_plugin
        )
        self.assertEqual(len(dependencies), 2)
        for dep in dependencies:
            self.assertIsInstance(dep, Plugin)

    @mock.patch.object(Plugins, "update_center_dict")
    @mock.patch.object(Plugins, "_poll")
    def test_plugin_version_already_installed(self, _poll_plugins, _update):
        _poll_plugins.return_value = self.DATA
        already_installed = Plugin(
            {"shortName": "subversion", "version": "1.45"}
        )
        self.assertTrue(
            self.J.plugins.plugin_version_already_installed(already_installed)
        )
        not_installed = Plugin({"shortName": "subversion", "version": "1.46"})
        self.assertFalse(
            self.J.plugins.plugin_version_already_installed(not_installed)
        )
        latest = Plugin({"shortName": "subversion", "version": "latest"})
        self.assertFalse(
            self.J.plugins.plugin_version_already_installed(latest)
        )

    @mock.patch.object(Plugins, "_poll")
    @mock.patch.object(
        Plugins,
        "update_center_install_status",
        new_callable=mock.mock.PropertyMock,
    )
    def test_restart_required_after_plugin_installation(
        self, status, _poll_plugins
    ):
        _poll_plugins.return_value = self.DATA
        status.return_value = {
            "data": {
                "jobs": [
                    {
                        "installStatus": "SuccessButRequiresRestart",
                        "name": "credentials",
                        "requiresRestart": "true",
                        "title": None,
                        "version": "0",
                    }
                ],
                "state": "RUNNING",
            },
            "status": "ok",
        }
        self.assertTrue(self.J.plugins.restart_required)

    @mock.patch.object(Plugins, "_poll")
    @mock.patch.object(
        Plugins,
        "update_center_install_status",
        new_callable=mock.mock.PropertyMock,
    )
    def test_restart_not_required_after_plugin_installation(
        self, status, _poll_plugins
    ):
        _poll_plugins.return_value = self.DATA
        status.return_value = {
            "data": {"jobs": [], "state": "RUNNING"},
            "status": "ok",
        }
        self.assertFalse(self.J.plugins.restart_required)

    def test_plugin_repr(self):
        p = Plugin(
            {
                "shortName": "subversion",
            }
        )
        self.assertEqual(repr(p), "<jenkinsapi.plugin.Plugin subversion>")


if __name__ == "__main__":
    unittest.main()
