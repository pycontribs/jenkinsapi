"""
System tests for Git SCM support in jenkinsapi.
"""

import pytest
from jenkinsapi_tests.test_utils.retry import retry
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import SCM_GIT_JOB

pytestmark = pytest.mark.docker


@retry()
def test_git_revision_lookup(jenkins):
    """Test that get_buildnumber_for_revision works with Git SHA1 hashes."""
    job_name = "git_revision_test_%s" % random_string()
    job = jenkins.create_job(job_name, SCM_GIT_JOB)

    # Trigger multiple builds to test revision lookup
    revisions = {}
    for build_num in range(1, 3):
        qq = job.invoke()
        qq.block_until_complete(delay=2)

        build = job.get_build(build_num)
        revision = build.get_revision()

        # Revision should be a string (SHA1 hash)
        assert isinstance(revision, str), f"Expected str, got {type(revision)}"
        assert len(revision) == 40, (
            f"Git SHA1 should be 40 chars, got {len(revision)}"
        )

        revisions[build_num] = revision

    # Test get_buildnumber_for_revision with Git SHA1
    # First revision should map to build 1
    found_builds = job.get_buildnumber_for_revision(revisions[1])
    assert 1 in found_builds, f"Build 1 should have revision {revisions[1]}"

    # Second revision should map to build 2
    found_builds = job.get_buildnumber_for_revision(revisions[2])
    assert 2 in found_builds, f"Build 2 should have revision {revisions[2]}"


@retry()
def test_get_revision_dict_skips_none(jenkins):
    """Test that get_revision_dict() doesn't include None revisions."""
    job_name = "git_revision_dict_test_%s" % random_string()
    job = jenkins.create_job(job_name, SCM_GIT_JOB)

    # Trigger a build
    qq = job.invoke()
    qq.block_until_complete(delay=2)

    # Get the revision dictionary
    rev_dict = job.get_revision_dict()

    # None should not be a key in the dictionary
    assert None not in rev_dict, (
        "Revision dictionary should not contain None key"
    )

    # Should have at least one valid revision
    assert len(rev_dict) > 0, (
        "Revision dictionary should have at least one entry"
    )

    # All keys should be strings (Git SHA1 hashes)
    for revision in rev_dict.keys():
        assert isinstance(revision, str), f"Expected str, got {type(revision)}"
        assert len(revision) == 40, (
            f"Git SHA1 should be 40 chars, got {len(revision)}"
        )
