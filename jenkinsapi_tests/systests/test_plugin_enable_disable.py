"""
System tests for Plugins.enable_plugin and Plugins.disable_plugin.
"""

import logging
import pytest

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker

# Use "mailer" - a leaf plugin with no test dependencies
SAFE_PLUGIN = "mailer"


def test_disable_plugin(jenkins):
    """Disable a plugin and verify its enabled state changes."""
    plugins = jenkins.get_plugins()
    assert SAFE_PLUGIN in plugins, "%s plugin not installed" % SAFE_PLUGIN

    plugins.disable_plugin(SAFE_PLUGIN)

    plugins.poll()
    plugin = plugins[SAFE_PLUGIN]
    assert not plugin.enabled, "Expected plugin to be disabled"


def test_enable_plugin(jenkins):
    """Disable then re-enable a plugin and verify enabled state."""
    plugins = jenkins.get_plugins()
    assert SAFE_PLUGIN in plugins, "%s plugin not installed" % SAFE_PLUGIN

    plugins.disable_plugin(SAFE_PLUGIN)
    plugins.poll()
    assert not plugins[SAFE_PLUGIN].enabled

    plugins.enable_plugin(SAFE_PLUGIN)
    plugins.poll()
    assert plugins[SAFE_PLUGIN].enabled, "Expected plugin to be re-enabled"
