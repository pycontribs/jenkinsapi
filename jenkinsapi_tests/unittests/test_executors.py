import pytest
from unittest import mock
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.executors import Executors
from jenkinsapi.executor import Executor


DATAM = {
    "assignedLabels": [{}],
    "description": None,
    "jobs": [],
    "mode": "NORMAL",
    "nodeDescription": "the master Jenkins node",
    "nodeName": "",
    "numExecutors": 2,
    "overallLoad": {},
    "primaryView": {"name": "All", "url": "http://localhost:8080/"},
    "quietingDown": False,
    "slaveAgentPort": 0,
    "unlabeledLoad": {},
    "useCrumbs": False,
    "useSecurity": False,
    "views": [
        {"name": "All", "url": "http://localhost:8080/"},
        {"name": "BigMoney", "url": "http://localhost:8080/view/BigMoney/"},
    ],
}

DATA0 = {
    "actions": [],
    "displayName": "host0.host.com",
    "executors": [{}, {}, {}, {}, {}, {}, {}, {}],
    "icon": "computer.png",
    "idle": False,
    "jnlpAgent": True,
    "launchSupported": False,
    "loadStatistics": {},
    "manualLaunchAllowed": True,
    "monitorData": {
        "hudson.node_monitors.SwapSpaceMonitor": {
            "availablePhysicalMemory": 8462417920,
            "availableSwapSpace": 0,
            "totalPhysicalMemory": 75858042880,
            "totalSwapSpace": 0,
        },
        "hudson.node_monitors.ArchitectureMonitor": "Linux (amd64)",
        "hudson.node_monitors.ResponseTimeMonitor": {"average": 2},
        "hudson.node_monitors.TemporarySpaceMonitor": {
            "path": "/tmp",
            "size": 430744551424,
        },
        "hudson.node_monitors.DiskSpaceMonitor": {
            "path": "/data/jenkins",
            "size": 1214028627968,
        },
        "hudson.node_monitors.ClockMonitor": {"diff": 1},
    },
    "numExecutors": 8,
    "offline": False,
    "offlineCause": None,
    "offlineCauseReason": "",
    "oneOffExecutors": [{}, {}],
    "temporarilyOffline": False,
}

DATA1 = {
    "actions": [],
    "displayName": "host1.host.com",
    "executors": [{}, {}],
    "icon": "computer.png",
    "idle": False,
    "jnlpAgent": True,
    "launchSupported": False,
    "loadStatistics": {},
    "manualLaunchAllowed": True,
    "monitorData": {
        "hudson.node_monitors.SwapSpaceMonitor": {
            "availablePhysicalMemory": 8462417920,
            "availableSwapSpace": 0,
            "totalPhysicalMemory": 75858042880,
            "totalSwapSpace": 0,
        },
        "hudson.node_monitors.ArchitectureMonitor": "Linux (amd64)",
        "hudson.node_monitors.ResponseTimeMonitor": {"average": 2},
        "hudson.node_monitors.TemporarySpaceMonitor": {
            "path": "/tmp",
            "size": 430744551424,
        },
        "hudson.node_monitors.DiskSpaceMonitor": {
            "path": "/data/jenkins",
            "size": 1214028627968,
        },
        "hudson.node_monitors.ClockMonitor": {"diff": 1},
    },
    "numExecutors": 2,
    "offline": False,
    "offlineCause": None,
    "offlineCauseReason": "",
    "oneOffExecutors": [{}, {}],
    "temporarilyOffline": False,
}

DATA2 = {
    "actions": [],
    "displayName": "host2.host.com",
    "executors": [{}, {}, {}, {}],
    "icon": "computer.png",
    "idle": False,
    "jnlpAgent": True,
    "launchSupported": False,
    "loadStatistics": {},
    "manualLaunchAllowed": True,
    "monitorData": {
        "hudson.node_monitors.SwapSpaceMonitor": {
            "availablePhysicalMemory": 8462417920,
            "availableSwapSpace": 0,
            "totalPhysicalMemory": 75858042880,
            "totalSwapSpace": 0,
        },
        "hudson.node_monitors.ArchitectureMonitor": "Linux (amd64)",
        "hudson.node_monitors.ResponseTimeMonitor": {"average": 2},
        "hudson.node_monitors.TemporarySpaceMonitor": {
            "path": "/tmp",
            "size": 430744551424,
        },
        "hudson.node_monitors.DiskSpaceMonitor": {
            "path": "/data/jenkins",
            "size": 1214028627968,
        },
        "hudson.node_monitors.ClockMonitor": {"diff": 1},
    },
    "numExecutors": 4,
    "offline": False,
    "offlineCause": None,
    "offlineCauseReason": "",
    "oneOffExecutors": [{}, {}],
    "temporarilyOffline": False,
}

DATA3 = {
    "actions": [],
    "displayName": "host3.host.com",
    "executors": [{}],
    "icon": "computer.png",
    "idle": False,
    "jnlpAgent": True,
    "launchSupported": False,
    "loadStatistics": {},
    "manualLaunchAllowed": True,
    "monitorData": {
        "hudson.node_monitors.SwapSpaceMonitor": {
            "availablePhysicalMemory": 8462417920,
            "availableSwapSpace": 0,
            "totalPhysicalMemory": 75858042880,
            "totalSwapSpace": 0,
        },
        "hudson.node_monitors.ArchitectureMonitor": "Linux (amd64)",
        "hudson.node_monitors.ResponseTimeMonitor": {"average": 2},
        "hudson.node_monitors.TemporarySpaceMonitor": {
            "path": "/tmp",
            "size": 430744551424,
        },
        "hudson.node_monitors.DiskSpaceMonitor": {
            "path": "/data/jenkins",
            "size": 1214028627968,
        },
        "hudson.node_monitors.ClockMonitor": {"diff": 1},
    },
    "numExecutors": 1,
    "offline": False,
    "offlineCause": None,
    "offlineCauseReason": "",
    "oneOffExecutors": [{}, {}],
    "temporarilyOffline": False,
}

EXEC0 = {
    "currentExecutable": {
        "number": 4168,
        "url": "http://localhost:8080/job/testjob/4168/",
    },
    "currentWorkUnit": {},
    "idle": False,
    "likelyStuck": False,
    "number": 0,
    "progress": 48,
}

EXEC1 = {
    "currentExecutable": None,
    "currentWorkUnit": None,
    "idle": True,
    "likelyStuck": False,
    "number": 0,
    "progress": -1,
}


@pytest.fixture(scope="function")
def jenkins(monkeypatch):
    def fake_poll(cls, tree=None):  # pylint: disable=unused-argument
        return DATAM

    monkeypatch.setattr(Jenkins, "_poll", fake_poll)
    return Jenkins("http://localhost:8080")


def test_repr(jenkins):
    # Can we produce a repr string for this object
    assert repr(jenkins)


def test_check_url(jenkins):
    assert jenkins.baseurl == "http://localhost:8080"


def test_get_executors(jenkins, monkeypatch):
    def fake_poll_extr(cls, tree=None):  # pylint: disable=unused-argument
        return EXEC0

    def fake_poll_extrs(cls, tree=None):  # pylint: disable=unused-argument
        return DATA3

    monkeypatch.setattr(Executor, "_poll", fake_poll_extr)
    monkeypatch.setattr(Executors, "_poll", fake_poll_extrs)

    exec_info = jenkins.get_executors(DATA3["displayName"])

    assert isinstance(exec_info, object)
    assert isinstance(repr(exec_info), str)

    for ex in exec_info:
        assert ex.get_progress() == 48, "Should return 48 %"


def testis_idle(jenkins, monkeypatch):
    def fake_poll_extr(cls, tree=None):  # pylint: disable=unused-argument
        return EXEC1

    def fake_poll_extrs(cls, tree=None):  # pylint: disable=unused-argument
        return DATA3

    monkeypatch.setattr(Executor, "_poll", fake_poll_extr)
    monkeypatch.setattr(Executors, "_poll", fake_poll_extrs)

    exec_info = jenkins.get_executors("host3.host.com")

    assert isinstance(exec_info, object)
    for ex in exec_info:
        assert ex.get_progress() == -1, "Should return 48 %"
        assert ex.is_idle() is True, "Should return True"
        assert repr(ex) == "<jenkinsapi.executor.Executor host3.host.com 0>"


@mock.patch.object(Executor, "_poll")
def test_likely_stuck(jenkins, monkeypatch):
    def fake_poll_extr(cls, tree=None):  # pylint: disable=unused-argument
        return EXEC0

    monkeypatch.setattr(Executor, "_poll", fake_poll_extr)

    baseurl = "http://localhost:8080/computer/host0.host.com/executors/0"
    nodename = "host0.host.com"
    single_executer = Executor(baseurl, nodename, jenkins, "0")
    assert single_executer.likely_stuck() is False


def test_get_current_executable(jenkins, monkeypatch):
    def fake_poll_extr(cls, tree=None):  # pylint: disable=unused-argument
        return EXEC0

    monkeypatch.setattr(Executor, "_poll", fake_poll_extr)

    baseurl = "http://localhost:8080/computer/host0.host.com/executors/0"
    nodename = "host0.host.com"
    single_executer = Executor(baseurl, nodename, jenkins, "0")
    assert single_executer.get_current_executable()["number"] == 4168
    assert (
        single_executer.get_current_executable()["url"]
        == "http://localhost:8080/job/testjob/4168/"
    )
