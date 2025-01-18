"""Module for custom_exceptions.

Where possible we try to throw exceptions with non-generic,
meaningful names.
"""


class JenkinsAPIException(Exception):
    """Base class for all errors"""

    pass


class NotFound(JenkinsAPIException):
    """Resource cannot be found"""

    pass


class ArtifactsMissing(NotFound):
    """Cannot find a build with all of the required artifacts."""

    pass


class UnknownJob(KeyError, NotFound):
    """Jenkins does not recognize the job requested."""

    pass


class UnknownView(KeyError, NotFound):
    """Jenkins does not recognize the view requested."""

    pass


class UnknownNode(KeyError, NotFound):
    """Jenkins does not recognize the node requested."""

    pass


class UnknownQueueItem(KeyError, NotFound):
    """Jenkins does not recognize the requested queue item"""

    pass


class UnknownPlugin(KeyError, NotFound):
    """Jenkins does not recognize the plugin requested."""

    pass


class NoBuildData(NotFound):
    """A job has no build data."""

    pass


class NotBuiltYet(NotFound):
    """A job has no build data."""

    pass


class ArtifactBroken(JenkinsAPIException):
    """An artifact is broken, wrong"""

    pass


class TimeOut(JenkinsAPIException):
    """Some jobs have taken too long to complete."""

    pass


class NoResults(JenkinsAPIException):
    """A build did not publish any results."""

    pass


class FailedNoResults(NoResults):
    """A build did not publish any results because it failed"""

    pass


class BadURL(ValueError, JenkinsAPIException):
    """A URL appears to be broken"""

    pass


class NotAuthorized(JenkinsAPIException):
    """Not Authorized to access resource"""

    # Usually thrown when we get a 403 returned
    pass


class NotSupportSCM(JenkinsAPIException):
    """
    It's a SCM that does not supported by current version of jenkinsapi
    """

    pass


class NotConfiguredSCM(JenkinsAPIException):
    """It's a job that doesn't have configured SCM"""

    pass


class NotInQueue(JenkinsAPIException):
    """It's a job that is not in the queue"""

    pass


class PostRequired(JenkinsAPIException):
    """Method requires POST and not GET"""

    pass


class BadParams(JenkinsAPIException):
    """Invocation was given bad or inappropriate params"""

    pass


class AlreadyExists(JenkinsAPIException):
    """
    Method requires POST and not GET
    """

    pass
