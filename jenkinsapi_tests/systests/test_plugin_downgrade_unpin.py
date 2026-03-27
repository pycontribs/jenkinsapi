"""
System tests for Plugins.downgrade_plugin and Plugins.unpin_plugin.

Note: downgrade and unpin are only meaningful when there is a previous
version to downgrade to, or the plugin is pinned. These tests verify
the API calls succeed without raising exceptions, since the test
Jenkins instance may not have a downgradable or pinned plugin available.
"""

import logging
import pytest

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker

# Use "mailer" as a safe leaf plugin
SAFE_PLUGIN = "mailer"


def test_unpin_plugin_does_not_raise(jenkins):
    """unpin_plugin should not raise even if the plugin is not pinned."""
    plugins = jenkins.get_plugins()
    assert SAFE_PLUGIN in plugins, "%s plugin not installed" % SAFE_PLUGIN
    # Unpin is a no-op if the plugin isn't pinned; should not raise
    plugins.unpin_plugin(SAFE_PLUGIN)


def test_downgrade_plugin_does_not_raise(jenkins):
    """downgrade_plugin should not raise if called on a non-downgradable plugin."""
    plugins = jenkins.get_plugins()
    assert SAFE_PLUGIN in plugins, "%s plugin not installed" % SAFE_PLUGIN
    # Downgrade is a no-op if there is no previous version; should not raise
    plugins.downgrade_plugin(SAFE_PLUGIN)
