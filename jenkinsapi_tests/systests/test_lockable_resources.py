from contextlib import ExitStack
from unittest import mock
import pytest

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.lockable_resources import (
    LockableResource,
    LockableResources,
    ResourceLockedError,
    ResourceReservationTimeoutError,
)
from jenkinsapi.utils.retry import SimpleRetryConfig

pytestmark = pytest.mark.docker

GROOVY_SCRIPT_INIT_TEST_RESOURCES = """
import org.jenkins.plugins.lockableresources.*

def manager = LockableResourcesManager.get()

// Reset to a clean slate before adding test resources
manager.resources.clear()

def resource = new LockableResource("locktest")
resource.setLabels("locktest")
manager.resources.add(resource)

def resource2 = new LockableResource("locktest2")
resource2.setLabels("locktest")
manager.resources.add(resource2)

manager.save()
"""


@pytest.fixture(scope="function")
def jenkins_test_lock_init(jenkins_admin_admin) -> None:
    """Fixture to create two lockable resources for testing."""
    jenkins_admin_admin.run_groovy_script(GROOVY_SCRIPT_INIT_TEST_RESOURCES)


@pytest.fixture
def test_lock_name() -> str:
    return "locktest"


@pytest.fixture
def test_lock_name2() -> str:
    return "locktest2"


@pytest.fixture
def test_lock_label() -> str:
    return "locktest"


# IMPORTANT: These fixtures use jenkins_admin_admin (not plain jenkins) because the
# lockable-resources plugin requires an authenticated non-anonymous user to perform
# reserve/unreserve actions. Requests from an anonymous user are silently accepted
# (HTTP 200) but the state change never takes effect. Security is enabled/disabled
# around each test by the jenkins_admin_admin fixture.
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


def test_reservation_by_name(
    lockable_resources: LockableResources,
    test_lock_name: str,
):
    reservation = lockable_resources.reservation_by_name(test_lock_name)
    assert lockable_resources.is_free(test_lock_name)
    with reservation:
        assert reservation.locked_resource_name == test_lock_name
        assert lockable_resources.is_free(test_lock_name) is False
        assert reservation.is_active()
    assert lockable_resources.is_free(test_lock_name)
    assert reservation.is_active() is False
    name = None
    with pytest.raises(RuntimeError):
        name = reservation.locked_resource_name
    assert name is None


def test_reservation_by_name_list(
    lockable_resources: LockableResources,
    test_lock_name: str,
    test_lock_name2: str,
):
    name_list = [test_lock_name, test_lock_name2]
    r1 = lockable_resources.reservation_by_name_list(name_list)
    assert lockable_resources.is_free(name_list[0])
    assert lockable_resources.is_free(name_list[1])
    with lockable_resources.reservation_by_name_list(name_list) as r1:
        assert r1.locked_resource_name == name_list[0]
        with lockable_resources.reservation_by_name_list(name_list) as r2:
            assert r2.locked_resource_name == name_list[1]
            assert lockable_resources.is_free(name_list[1]) is False
        assert lockable_resources.is_free(name_list[1])
    assert lockable_resources.is_free(name_list[0])
    assert lockable_resources.is_free(name_list[1])


def test_reservation_by_label(
    lockable_resources: LockableResources,
    test_lock_label: str,
):
    res = lockable_resources.reservation_by_label(test_lock_label)
    with res:
        locked_resource = lockable_resources[res.locked_resource_name]
        assert locked_resource.is_free() is False
        assert test_lock_label in locked_resource.data["labelsAsList"]
    assert locked_resource.is_free() is True


def test_custom_retry(
    lockable_resources: LockableResources,
    test_lock_name: str,
):
    with ExitStack() as exit_stack:
        exit_stack.enter_context(
            mock.patch(
                "time.monotonic",
                side_effect=range(1000, 10000),
            )
        )
        mock_time_sleep = exit_stack.enter_context(
            mock.patch("time.sleep"),
        )
        mock_try_reserve = exit_stack.enter_context(
            mock.patch.object(
                lockable_resources,
                "try_reserve",
                return_value=None,
            )
        )
        mock_poll = exit_stack.enter_context(
            mock.patch.object(
                lockable_resources,
                "poll",
            )
        )
        exit_stack.enter_context(
            pytest.raises(ResourceReservationTimeoutError)
        )
        with lockable_resources.reservation_by_name(
            test_lock_name,
            retry=SimpleRetryConfig(
                sleep_period=1,
                timeout=5.5,
            ),
        ):
            pass
    assert mock_time_sleep.call_count == 5
    assert mock_try_reserve.call_count == 6
    assert mock_poll.call_count == 5
