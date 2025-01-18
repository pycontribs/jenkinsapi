"""
System tests for `jenkinsapi.plugins` module.
"""

import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi.plugin import Plugin

log = logging.getLogger(__name__)


def test_plugin_data(jenkins):
    # It takes time to get plugins json from remote
    timeout = jenkins.requester.timeout
    jenkins.requester.timeout = 60
    jenkins.plugins.check_updates_server()
    jenkins.requester.timeout = timeout

    assert "mailer" in jenkins.plugins


def test_get_missing_plugin(jenkins):
    plugins = jenkins.get_plugins()
    with pytest.raises(KeyError):
        plugins["lsdajdaslkjdlkasj"]  # this plugin surely does not exist!


def test_get_single_plugin(jenkins):
    plugins = jenkins.get_plugins()
    plugin_name, plugin = next(plugins.iteritems())

    assert isinstance(plugin_name, str)
    assert isinstance(plugin, Plugin)


def test_get_single_plugin_depth_2(jenkins):
    plugins = jenkins.get_plugins(depth=2)
    _, plugin = next(plugins.iteritems())

    assert isinstance(plugin, Plugin)


def test_delete_inexistant_plugin(jenkins):
    with pytest.raises(KeyError):
        del jenkins.plugins[random_string()]


#    def test_install_uninstall_plugin(jenkins):
#        plugin_name = "suppress-stack-trace"
#
#        plugin_dict = {
#            "shortName": plugin_name,
#            "version": "latest",
#        }
#        jenkins.plugins[plugin_name] = Plugin(plugin_dict)
#
#        assert plugin_name in jenkins.plugins
#
#        plugin = jenkins.get_plugins()[plugin_name]
#        assert isinstance(plugin, Plugin)
#        assert plugin.shortName == plugin_name
#
#        del jenkins.plugins[plugin_name]
#        assert jenkins.plugins[plugin_name].deleted
#
#
#    def test_install_multiple_plugins(jenkins):
#        plugin_one_name = "keyboard-shortcuts-plugin"
#        plugin_one_version = "latest"
#        plugin_one = "@".join((plugin_one_name, plugin_one_version))
#        plugin_two = Plugin(
#            {"shortName": "emotional-jenkins-plugin", "version": "latest"}
#        )
#
#        assert isinstance(plugin_two, Plugin)
#
#        plugin_list = [plugin_one, plugin_two]
#
#        jenkins.install_plugins(plugin_list)
#
#        assert plugin_one_name in jenkins.plugins
#        assert plugin_two.shortName in jenkins.plugins
#
#        del jenkins.plugins["keyboard-shortcuts-plugin"]
#        del jenkins.plugins["emotional-jenkins-plugin"]
#
#
#    def test_downgrade_plugin(jenkins):
#        plugin_name = "console-badge"
#        plugin_version = "latest"
#        plugin = Plugin({"shortName": plugin_name, "version": plugin_version})
#
#        assert isinstance(plugin, Plugin)
#
#        # Need to restart when not installing the latest version
#        jenkins.install_plugins([plugin])
#
#        installed_plugin = jenkins.plugins[plugin_name]
#
#        assert installed_plugin.version == "1.1"
#
#        older_plugin = Plugin({"shortName": plugin_name, "version": "1.0"})
#        jenkins.install_plugins(
#            [older_plugin], restart=True, wait_for_reboot=True)
#        installed_older_plugin = jenkins.plugins[plugin_name]
#
#        assert installed_older_plugin.version == "1.0"
#
#        del jenkins.plugins[plugin_name]
