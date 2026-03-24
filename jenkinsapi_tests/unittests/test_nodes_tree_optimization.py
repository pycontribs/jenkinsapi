"""
Tests for issue #855: Nodes class should limit API requests with tree parameter.

On large Jenkins instances with many nodes, fetching all node data times out.
Using tree=computer[displayName] restricts the response and avoids timeouts.
"""

import pytest
from unittest.mock import MagicMock
import requests

from jenkinsapi.nodes import Nodes


class MockResponse(requests.Response):
    def __init__(self, content):
        super().__init__()
        self.status_code = 200
        self._content = content
        self.encoding = "utf-8"


def test_nodes_poll_uses_tree_parameter(monkeypatch):
    """Nodes._poll() must use tree=computer[displayName] to reduce payload."""
    captured_calls = []

    def fake_get_data(self, url, params=None, tree=None):
        captured_calls.append({"url": url, "params": params, "tree": tree})
        return {"computer": [{"displayName": "node1"}]}

    monkeypatch.setattr(
        "jenkinsapi.jenkinsbase.JenkinsBase.get_data", fake_get_data
    )

    jenkins_mock = MagicMock()
    nodes = Nodes("http://dummy/computer", jenkins_mock)
    nodes.poll()

    assert len(captured_calls) > 0, "get_data was not called"
    call = captured_calls[0]
    assert call["tree"] == "computer[displayName]", (
        f"Expected tree='computer[displayName]', got tree={call['tree']}"
    )


def test_nodes_default_tree_when_none_specified(monkeypatch):
    """Nodes must use the default tree=computer[displayName] when poll() is called without tree."""
    captured_calls = []

    def fake_get_data(self, url, params=None, tree=None):
        captured_calls.append({"tree": tree})
        return {"computer": [{"displayName": "node1"}]}

    monkeypatch.setattr(
        "jenkinsapi.jenkinsbase.JenkinsBase.get_data", fake_get_data
    )

    jenkins_mock = MagicMock()
    nodes = Nodes("http://dummy/computer", jenkins_mock)
    nodes.poll()  # No tree specified

    call = captured_calls[0]
    assert call["tree"] == "computer[displayName]", (
        f"Expected default tree to be 'computer[displayName]', got {call['tree']}"
    )
