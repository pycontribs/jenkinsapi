import pytest

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.lockable_resources import (
    LockableResource,
    LockableResources,
    ResourceLockedError,
)
from jenkinsapi.utils.jenkins_launcher import JenkinsLancher

GROOVY_SCRIPT_INIT_TEST_RESOURCES = """
import org.jenkins.plugins.lockableresources.*

def manager = LockableResourcesManager.get()

def resource = new LockableResource("locktest")
resource.setLabels(["locktest"])
manager.resources.add(resource)

def resource2 = new LockableResource("locktest2")
resource2.setLabels(["locktest"])
manager.resources.add(resource2)

manager.save()
"""


@pytest.fixture(scope="module")
def jenkins_test_lock_init(launched_jenkins: JenkinsLancher) -> None:
    """Fixture to create two lockable resources for testing."""
    jenkins = Jenkins(launched_jenkins.jenkins_url, timeout=30)
    jenkins.run_groovy_script(GROOVY_SCRIPT_INIT_TEST_RESOURCES)


@pytest.fixture
def test_lock_name() -> str:
    return "locktest"


@pytest.fixture(scope="function")
def lockable_resources(
    jenkins_admin_admin: Jenkins,
    jenkins_test_lock_init: None,  # pylint: disable=unused-argument
) -> LockableResources:
    return jenkins_admin_admin.get_lockable_resources()


def test_list_lockables(lockable_resources: LockableResources):
    assert isinstance(str(lockable_resources), str)
    assert isinstance(repr(lockable_resources), str)

    # iter names
    for name in lockable_resources:
        res = lockable_resources[name]
        assert isinstance(res, LockableResource)
        assert isinstance(res.is_free(), bool)
        assert isinstance(res.is_reserved(), bool)
        assert isinstance(res.data["description"], str)
    # iter values directly
    for res in lockable_resources.values():
        assert isinstance(res, LockableResource)
    assert len(lockable_resources) == len(lockable_resources.values())


def test_reserve_unreserve(
    lockable_resources: LockableResources,
    test_lock_name: str,
):
    rn = test_lock_name
    assert rn in lockable_resources
    assert lockable_resources.is_reserved(rn) is False

    lockable_resources.reserve(rn)
    assert lockable_resources.is_reserved(rn) is True

    with pytest.raises(ResourceLockedError):
        lockable_resources.reserve(rn)

    lockable_resources.unreserve(rn)
    assert lockable_resources.is_reserved(rn) is False


def test_reserve_unreserve_nopoll(
    lockable_resources: LockableResources,
    test_lock_name: str,
):
    lockable_resources.poll_after_post = False
    rn = test_lock_name
    assert rn in lockable_resources
    assert lockable_resources.is_reserved(rn) is False

    lockable_resources.reserve(rn)
    assert lockable_resources.is_reserved(rn) is False
    lockable_resources.poll()
    assert lockable_resources.is_reserved(rn) is True

    with pytest.raises(ResourceLockedError):
        lockable_resources.reserve(rn)

    lockable_resources.unreserve(rn)
    assert lockable_resources.is_reserved(rn) is True
    lockable_resources.poll()
    assert lockable_resources.is_reserved(rn) is False
