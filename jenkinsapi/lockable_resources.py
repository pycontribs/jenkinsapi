from abc import ABC, abstractmethod
import logging
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    TypedDict,
)

from requests import Response

from jenkinsapi.custom_exceptions import JenkinsAPIException
from jenkinsapi.jenkinsbase import JenkinsBase
from jenkinsapi.utils.retry import RetryConfig, SimpleRetryConfig

if TYPE_CHECKING:
    from jenkinsapi.jenkins import Jenkins
logger = logging.getLogger(__name__)


class LockableResourcePropertyDict(TypedDict):
    """Property of a lockable resource, as returned by Jenkins API"""

    name: str
    value: str


class LockableResourceDict(TypedDict, total=False):
    """
    Dictionary representation of a lockable resource

    This is exactly as returned by Jenkins API
    """

    name: str
    description: str
    note: str

    labels: str
    labelsAsList: List[str]
    properties: List[LockableResourcePropertyDict]

    free: bool
    stolen: bool
    lockCause: Optional[str]
    locked: bool

    ephemeral: bool

    reserved: bool
    reservedBy: Optional[str]
    reservedByEmail: Optional[str]
    reservedTimestamp: Optional[int]

    buildName: Optional[str]


class LockableResource:
    """Object representation of a lockable resource"""

    def __init__(self, parent: "LockableResources", name: str):
        self.parent = parent
        self.name = name

    @property
    def data(self) -> LockableResourceDict:
        return self.parent.data_dict[self.name]

    def is_free(self) -> bool:
        """
        Check if the resource is free for reservation

        This is what the java plugin implementation checks internally
        """
        return self.data["free"]

    def is_reserved(self) -> bool:
        return self.data["reserved"]

    def reserve(self) -> None:
        self.parent.reserve(self.name)

    def unreserve(self) -> None:
        self.parent.unreserve(self.name)


#: Specific HTTP status code returned by API when resource is locked
HTTP_STATUS_CODE_LOCKED = 423


class ResourceLockedError(JenkinsAPIException):
    """Raised when a resource is locked and cannot be reserved"""

    pass


class ResourceReservationTimeoutError(JenkinsAPIException, TimeoutError):
    """Raised when resource reservation times out"""

    pass


DEFAULT_WAIT_SLEEP_PERIOD = 5
DEFAULT_WAIT_TIMEOUT_PERIOD = 3600
DEFAULT_RETRY_CONFIG = SimpleRetryConfig(
    sleep_period=DEFAULT_WAIT_SLEEP_PERIOD,
    timeout=DEFAULT_WAIT_TIMEOUT_PERIOD,
)


class LockableResources(JenkinsBase, Mapping[str, LockableResource]):
    """Object representation of the lockable resource jenkins API"""

    jenkins: "Jenkins"

    poll_after_post: bool
    """
    If true then poll again after every successful post request

    This ensure that resource properties are up-to-date after any changes.
    Setting this to False would require manual poll() calls but could be more
    efficient in advanced scenarios with careful usage.
    """

    def __init__(
        self,
        jenkins_obj: "Jenkins",
        poll=True,
        poll_after_post: bool = True,
    ):
        self.jenkins = jenkins_obj
        baseurl = jenkins_obj.baseurl + "/lockable-resources/api/python"
        JenkinsBase.__init__(self, baseurl, poll=poll)
        self.poll_after_post = poll_after_post

    def __str__(self) -> str:
        return f"Lockable Resources @ {self.baseurl}"

    def get_jenkins_obj(self) -> "Jenkins":
        return self.jenkins

    def poll(self, tree=None) -> None:
        super().poll(tree)
        self._data_dict = None

    @property
    def data_list(self) -> List[LockableResourceDict]:
        """API data as a list of `LockableResourceDict`"""
        if self._data is None:
            raise ValueError("need poll")
        return self._data["resources"]

    _data_dict: Optional[Dict[str, LockableResourceDict]] = None

    @property
    def data_dict(self) -> Dict[str, LockableResourceDict]:
        """API data as a dict mapping name to `LockableResourceDict`"""
        if self._data_dict is None:
            self._data_dict = {item["name"]: item for item in self.data_list}
        return self._data_dict

    def __len__(self) -> int:
        return len(self.data_list)

    def __iter__(self):
        return iter(self.data_dict)

    def __getitem__(self, name: str) -> LockableResource:
        return LockableResource(self, name)

    def is_free(self, name: str) -> bool:
        return self.data_dict[name]["free"]

    def is_reserved(self, name: str) -> bool:
        return self.data_dict[name]["reserved"]

    def _make_resource_request(
        self,
        req: str,
        name: str,
    ) -> Response:
        """Make a resource-specific request via HTTP POST"""
        response = self.jenkins.requester.post_and_confirm_status(
            self.jenkins.baseurl + f"/lockable-resources/{req}",
            data=dict(resource=name),
            valid=[
                200,
                HTTP_STATUS_CODE_LOCKED,
            ],
        )
        if response.status_code == HTTP_STATUS_CODE_LOCKED:
            raise ResourceLockedError(
                f"Resource {name} is busy or reserved by another user."
            )
        if self.poll_after_post:
            self.poll()
        return response

    def reserve(self, name: str) -> None:
        self._make_resource_request("reserve", name)

    def unreserve(self, name: str) -> None:
        self._make_resource_request("unreserve", name)

    def try_reserve(
        self,
        selector: "ResourceSelector",
    ) -> Optional[str]:
        """
        Try to reserve a resource that matches the given condition

        :return: the name of the reserved resource on success
        :return: None if all resources are busy
        """
        for resource_name in selector.select(self):
            resource = self[resource_name]
            # if server reported that the resource is not free
            # don't try to reserve it
            if not resource.is_free():
                continue
            # if server reported that the resource is free
            # it might have been reserved since the last poll
            try:
                resource.reserve()
            except ResourceLockedError:
                continue
            return resource.name
        return None

    def wait_reserve(
        self,
        selector: "ResourceSelector",
        retry: RetryConfig = DEFAULT_RETRY_CONFIG,
    ) -> str:
        """
        Wait for a resource that matches the given condition to become available

        :return: the name of the reserved resource on success
        :raise ResourceReservationTimeoutError: if no matching resources are found during the timeout period.
        """
        retry_state = retry.begin()
        while True:
            result = self.try_reserve(selector)
            if result is not None:
                return result
            try:
                retry_state.check_retry()
            except TimeoutError as err:
                raise ResourceReservationTimeoutError(
                    f"Timeout waiting for a resource matching {selector} after {retry}"
                ) from err
            logger.info("No free resources matching %r, retry", selector)
            self.poll()

    def reservation_by_label(
        self,
        label: str,
        retry: RetryConfig = DEFAULT_RETRY_CONFIG,
    ) -> "LockedResourceReservation":
        return LockedResourceReservation(
            self,
            ResourceLabelSelector(label),
            retry=retry,
        )

    def reservation_by_name(
        self,
        name: str,
        retry: RetryConfig = DEFAULT_RETRY_CONFIG,
    ) -> "LockedResourceReservation":
        return LockedResourceReservation(
            self,
            ResourceNameSelector(name),
            retry=retry,
        )

    def reservation_by_name_list(
        self,
        name_list: List[str],
        retry: RetryConfig = DEFAULT_RETRY_CONFIG,
    ) -> "LockedResourceReservation":
        return LockedResourceReservation(
            self,
            ResourceNameListSelector(name_list),
            retry=retry,
        )


class ResourceSelector(ABC):
    """Base class for which iterates acceptable resources for a reservation"""

    @abstractmethod
    def select(self, lockable_resources: LockableResources) -> Iterator[str]:
        """Iterate acceptable resource names"""
        pass


class ResourceNameSelector(ResourceSelector):
    """Implementation of :py:class:`ResourceSelector` that selects a single resource by name"""

    def __init__(self, name: str):
        self.name = name

    def select(self, lockable_resources: LockableResources) -> Iterator[str]:
        yield self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


class ResourceNameListSelector(ResourceSelector):
    """Implementation of :py:class:`ResourceSelector` that selects from a list of resources"""

    def __init__(self, name_list: List[str]):
        self.name_list = name_list

    def select(self, lockable_resources: LockableResources) -> Iterator[str]:
        return iter(self.name_list)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name_list!r})"


class ResourceLabelSelector(ResourceSelector):
    """Implementation of :py:class:`ResourceSelector` that selects any resources with a given jenkins label"""

    def __init__(self, label: str):
        self.label = label

    def select(self, lockable_resources: LockableResources) -> Iterator[str]:
        for resource in lockable_resources.values():
            if self.label in resource.data["labelsAsList"]:
                yield resource.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.label!r})"


class LockedResourceReservation:
    """
    Context manager for locking a Jenkins resource

    Creating this object does not lock the resource, it is only locked and
    unlocked on :meth:`__enter__` and :meth:`__exit__` methods.

    Example::

        reservation: LockedResourceReservation = init_reservation()
        # .. possibly much later ...
        print("Resource will be locked ...")
        with reservation as locked_resource:
            name = locked_resource.locked_resource_name
            print(f"Resource currently locked: {name}")
        print("Resource no longer locked")

    If resources are busy this will retry until it will eventually succeed or time out.

    :raise ResourceReservationTimeoutError: if reservation process times out
    """

    _locked_resource_name: Optional[str] = None
    retry: RetryConfig

    def __init__(
        self,
        api: LockableResources,
        selector: ResourceSelector,
        retry: RetryConfig = DEFAULT_RETRY_CONFIG,
    ):
        self.api = api
        self.selector = selector
        self.retry = retry

    def is_active(self) -> bool:
        """Check if the resource is currently locked"""
        return self._locked_resource_name is not None

    @property
    def locked_resource_name(self) -> str:
        """
        Return the name of the locked resource

        This throws an error if the resource is not currently locked.
        """
        if self._locked_resource_name is None:
            raise RuntimeError("Resource not locked")
        return self._locked_resource_name

    def __enter__(self) -> "LockedResourceReservation":
        """Acquire a lock for the specified label."""
        if self._locked_resource_name is not None:
            raise RuntimeError("Lock already acquired")
        self._locked_resource_name = self.api.wait_reserve(
            self.selector, retry=self.retry
        )
        return self

    def __exit__(self, *a) -> None:
        if self._locked_resource_name is not None:
            self.api.unreserve(self._locked_resource_name)
            self._locked_resource_name = None
