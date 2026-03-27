"""
System tests for Jenkins.reload - reloads configuration from disk.
"""

import logging
import pytest

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def test_reload(jenkins):
    """Reload Jenkins configuration and verify it remains accessible."""
    jenkins.poll()
    jenkins.reload()
    # Jenkins should still be reachable after reload
    jenkins.poll()
