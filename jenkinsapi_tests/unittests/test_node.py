import pytest
from jenkinsapi.node import Node

# Import monitor field mappings for use in tests
MONITOR_FIELDS = Node._MONITOR_FIELDS


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


def get_monitor_expected_value(field_key: str) -> any:
    """Helper to get expected value from DATA using MONITOR_FIELDS config."""
    config = MONITOR_FIELDS[field_key]
    monitor_key = f"hudson.node_monitors.{config['monitor']}"
    return DATA["monitorData"][monitor_key][config["field"]]


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


@pytest.mark.parametrize(
    "field_key,method_name",
    [
        ("available_physical_memory", "get_available_physical_memory"),
        ("available_swap_space", "get_available_swap_space"),
        ("total_physical_memory", "get_total_physical_memory"),
        ("total_swap_space", "get_total_swap_space"),
        ("workspace_path", "get_workspace_path"),
        ("workspace_size", "get_workspace_size"),
        ("temp_path", "get_temp_path"),
        ("temp_size", "get_temp_size"),
        ("response_time", "get_response_time"),
        ("clock_difference", "get_clock_difference"),
    ],
)
def test_monitor_methods(node, field_key, method_name):
    """Test monitor getter methods retrieve correct values from monitorData."""
    expected = get_monitor_expected_value(field_key)
    result = getattr(node, method_name)()
    assert result == expected


def test_architecture(node):
    expected_value = DATA["monitorData"][
        "hudson.node_monitors.ArchitectureMonitor"
    ]
    assert node.get_architecture() == expected_value


@pytest.mark.parametrize(
    "field_key",
    [
        "available_physical_memory",
        "workspace_path",
        "response_time",
        "clock_difference",
        "temp_path",
    ],
)
def test_get_monitor_data(node, field_key):
    """Test get_monitor_data helper retrieves correct monitor field values."""
    config = MONITOR_FIELDS[field_key]
    result = node.get_monitor_data(config["monitor"], config["field"])
    assert result == get_monitor_expected_value(field_key)


def test_get_monitor_data_with_poll_false(node):
    """Test get_monitor_data with poll_monitor=False uses cached data."""
    config = MONITOR_FIELDS["temp_path"]
    result = node.get_monitor_data(
        config["monitor"], config["field"], poll_monitor=False
    )
    assert result == get_monitor_expected_value("temp_path")


def test_get_monitor_data_nonexistent_monitor(node):
    """Test get_monitor_data raises AssertionError for non-existent monitor"""
    with pytest.raises(AssertionError):
        node.get_monitor_data("NonExistentMonitor", "some_key")
