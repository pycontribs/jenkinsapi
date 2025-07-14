import logging
from typing import TYPE_CHECKING, Dict, List, Mapping, Optional, TypedDict

from jenkinsapi.custom_exceptions import JenkinsAPIException
from jenkinsapi.jenkinsbase import JenkinsBase
from requests import Response

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
