import pytest
from jenkinsapi.node import Node


DATA = {
    "actions": [],
    "displayName": "bobnit",
    "executors": [{}],
    "icon": "computer.png",
    "idle": True,
    "jnlpAgent": False,
    "launchSupported": True,
    "loadStatistics": {},
    "manualLaunchAllowed": True,
    "monitorData": {
        "hudson.node_monitors.SwapSpaceMonitor": {
            "availablePhysicalMemory": 7681417216,
            "availableSwapSpace": 12195983360,
            "totalPhysicalMemory": 8374497280,
            "totalSwapSpace": 12195983360,
        },
        "hudson.node_monitors.ArchitectureMonitor": "Linux (amd64)",
        "hudson.node_monitors.ResponseTimeMonitor": {"average": 64},
        "hudson.node_monitors.TemporarySpaceMonitor": {
            "path": "/tmp",
            "size": 250172776448,
        },
        "hudson.node_monitors.DiskSpaceMonitor": {
            "path": "/home/sal/jenkins",
            "size": 170472026112,
        },
        "hudson.node_monitors.ClockMonitor": {"diff": 6736},
    },
    "numExecutors": 1,
    "offline": False,
    "offlineCause": None,
    "oneOffExecutors": [],
    "temporarilyOffline": False,
}


@pytest.fixture(scope="function")
def node(monkeypatch, mocker):
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return DATA

    monkeypatch.setattr(Node, "_poll", fake_poll)
    jenkins = mocker.MagicMock()

    return Node(jenkins, "http://foo:8080", "bobnit", {})


def test_repr(node):
    # Can we produce a repr string for this object
    repr(node)


def test_name(node):
    with pytest.raises(AttributeError):
        node.id()
    assert node.name == "bobnit"


def test_online(node):
    assert node.is_online() is True


def test_available_physical_memory(node):
    monitor = DATA["monitorData"]["hudson.node_monitors.SwapSpaceMonitor"]
    expected_value = monitor["availablePhysicalMemory"]
    assert node.get_available_physical_memory() == expected_value


def test_available_swap_space(node):
    monitor = DATA["monitorData"]["hudson.node_monitors.SwapSpaceMonitor"]
    expected_value = monitor["availableSwapSpace"]
    assert node.get_available_swap_space() == expected_value


def test_total_physical_memory(node):
    monitor = DATA["monitorData"]["hudson.node_monitors.SwapSpaceMonitor"]
    expected_value = monitor["totalPhysicalMemory"]
    assert node.get_total_physical_memory() == expected_value


def test_total_swap_space(node):
    monitor = DATA["monitorData"]["hudson.node_monitors.SwapSpaceMonitor"]
    expected_value = monitor["totalSwapSpace"]
    assert node.get_total_swap_space() == expected_value


def test_workspace_path(node):
    monitor = DATA["monitorData"]["hudson.node_monitors.DiskSpaceMonitor"]
    expected_value = monitor["path"]
    assert node.get_workspace_path() == expected_value


def test_workspace_size(node):
    monitor = DATA["monitorData"]["hudson.node_monitors.DiskSpaceMonitor"]
    expected_value = monitor["size"]
    assert node.get_workspace_size() == expected_value


def test_temp_path(node):
    monitor = DATA["monitorData"]["hudson.node_monitors.TemporarySpaceMonitor"]
    expected_value = monitor["path"]
    assert node.get_temp_path() == expected_value


def test_temp_size(node):
    monitor = DATA["monitorData"]["hudson.node_monitors.TemporarySpaceMonitor"]
    expected_value = monitor["size"]
    assert node.get_temp_size() == expected_value


def test_architecture(node):
    expected_value = DATA["monitorData"][
        "hudson.node_monitors.ArchitectureMonitor"
    ]
    assert node.get_architecture() == expected_value


def test_response_time(node):
    monitor = DATA["monitorData"]["hudson.node_monitors.ResponseTimeMonitor"]
    expected_value = monitor["average"]
    assert node.get_response_time() == expected_value


def test_clock_difference(node):
    monitor = DATA["monitorData"]["hudson.node_monitors.ClockMonitor"]
    expected_value = monitor["diff"]
    assert node.get_clock_difference() == expected_value


def test_get_monitor_data_swap_space(node):
    """Test get_monitor_data helper retrieves SwapSpaceMonitor data"""
    result = node.get_monitor_data(
        "SwapSpaceMonitor", "availablePhysicalMemory"
    )
    expected = DATA["monitorData"]["hudson.node_monitors.SwapSpaceMonitor"][
        "availablePhysicalMemory"
    ]
    assert result == expected


def test_get_monitor_data_disk_space(node):
    """Test get_monitor_data helper retrieves DiskSpaceMonitor data"""
    result = node.get_monitor_data("DiskSpaceMonitor", "path")
    expected = DATA["monitorData"]["hudson.node_monitors.DiskSpaceMonitor"][
        "path"
    ]
    assert result == expected


def test_get_monitor_data_response_time(node):
    """Test get_monitor_data helper retrieves ResponseTimeMonitor data"""
    result = node.get_monitor_data("ResponseTimeMonitor", "average")
    expected = DATA["monitorData"]["hudson.node_monitors.ResponseTimeMonitor"][
        "average"
    ]
    assert result == expected


def test_get_monitor_data_clock(node):
    """Test get_monitor_data helper retrieves ClockMonitor data"""
    result = node.get_monitor_data("ClockMonitor", "diff")
    expected = DATA["monitorData"]["hudson.node_monitors.ClockMonitor"]["diff"]
    assert result == expected


def test_get_monitor_data_with_poll_false(node):
    """Test get_monitor_data with poll_monitor=False uses cached data"""
    result = node.get_monitor_data(
        "TemporarySpaceMonitor", "path", poll_monitor=False
    )
    expected = DATA["monitorData"][
        "hudson.node_monitors.TemporarySpaceMonitor"
    ]["path"]
    assert result == expected


def test_get_monitor_data_nonexistent_monitor(node):
    """Test get_monitor_data raises AssertionError for non-existent monitor"""
    with pytest.raises(AssertionError):
        node.get_monitor_data("NonExistentMonitor", "some_key")
