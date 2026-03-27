"""
System tests for Node.change_mode - switch between NORMAL and EXCLUSIVE.
"""

import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


@pytest.fixture
def slave_node(jenkins, request):
    """Create a JNLP slave node and remove it after the test."""
    node_name = "test-node-%s" % random_string()
    node = jenkins.create_node(node_name, labels="test")

    def cleanup():
        if jenkins.has_node(node_name):
            jenkins.delete_node(node_name)

    request.addfinalizer(cleanup)
    return node


def test_change_mode_to_exclusive(slave_node):
    """Change node mode from NORMAL to EXCLUSIVE."""
    slave_node.change_mode("EXCLUSIVE")
    config = slave_node.get_config()
    assert "<mode>EXCLUSIVE</mode>" in config


def test_change_mode_to_normal(slave_node):
    """Change node mode to EXCLUSIVE then back to NORMAL."""
    slave_node.change_mode("EXCLUSIVE")
    slave_node.change_mode("NORMAL")
    config = slave_node.get_config()
    assert "<mode>NORMAL</mode>" in config


def test_change_mode_invalid(slave_node):
    """Invalid mode raises ValueError."""
    with pytest.raises(ValueError, match="NORMAL.*EXCLUSIVE"):
        slave_node.change_mode("INVALID")
