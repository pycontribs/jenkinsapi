import jenkinsapi


def test_jenkinsapi_version():
    """Verify that we can get the jenkinsapi version number from the
    package's __version__ property.
    """
    version = jenkinsapi.__version__
    # only first two parts must be interger, 1.0.dev5 being a valid version.
    parts = [int(x) for x in version.split(".")[0:2]]
    for part in parts:
        assert part >= 0, "Implausible version number: %r" % version
