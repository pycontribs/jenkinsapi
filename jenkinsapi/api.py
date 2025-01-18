"""
This module is a collection of helpful, high-level functions
for automating common tasks.
Many of these functions were designed to be exposed to the command-line,
hence they have simple string arguments.
"""

import os
import re
import time
import logging
from typing import List, Dict

from urllib.parse import urlparse

from jenkinsapi import constants
from jenkinsapi.artifact import Artifact
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.view import View
from jenkinsapi.job import Job
from jenkinsapi.build import Build
from jenkinsapi.custom_exceptions import ArtifactsMissing, TimeOut, BadURL
from jenkinsapi.result_set import ResultSet

log: logging.Logger = logging.getLogger(__name__)


def get_latest_test_results(
    jenkinsurl: str,
    jobname: str,
    username: str = "",
    password: str = "",
    ssl_verify: bool = True,
) -> ResultSet:
    """
    A convenience function to fetch down the very latest test results
    from a jenkins job.
    """
    latestbuild: Build = get_latest_build(
        jenkinsurl,
        jobname,
        username=username,
        password=password,
        ssl_verify=ssl_verify,
    )
    return latestbuild.get_resultset()


def get_latest_build(
    jenkinsurl: str,
    jobname: str,
    username: str = "",
    password: str = "",
    ssl_verify: bool = True,
) -> Build:
    """
    A convenience function to fetch down the very latest test results
    from a jenkins job.
    """
    jenkinsci: Jenkins = Jenkins(
        jenkinsurl, username=username, password=password, ssl_verify=ssl_verify
    )
    job: Job = jenkinsci[jobname]
    return job.get_last_build()


def get_latest_complete_build(
    jenkinsurl: str,
    jobname: str,
    username: str = "",
    password: str = "",
    ssl_verify: bool = True,
) -> Build:
    """
    A convenience function to fetch down the very latest test results
    from a jenkins job.
    """
    jenkinsci: Jenkins = Jenkins(
        jenkinsurl, username=username, password=password, ssl_verify=ssl_verify
    )
    job: Job = jenkinsci[jobname]
    return job.get_last_completed_build()


def get_build(
    jenkinsurl: str,
    jobname: str,
    build_no: int,
    username: str = "",
    password: str = "",
    ssl_verify: bool = True,
) -> Build:
    """
    A convenience function to fetch down the test results
    from a jenkins job by build number.
    """
    jenkinsci = Jenkins(
        jenkinsurl, username=username, password=password, ssl_verify=ssl_verify
    )
    job = jenkinsci[jobname]
    return job.get_build(build_no)


def get_artifacts(
    jenkinsurl: str,
    jobname: str,
    build_no: int,
    username: str = "",
    password: str = "",
    ssl_verify: bool = True,
):
    """
    Find all the artifacts for the latest build of a job.
    """
    jenkinsci = Jenkins(
        jenkinsurl, username=username, password=password, ssl_verify=ssl_verify
    )
    job = jenkinsci[jobname]
    if build_no:
        build = job.get_build(build_no)
    else:
        build = job.get_last_good_build()
    artifacts = build.get_artifact_dict()
    log.info(
        msg=f"Found {len(artifacts.keys())} \
        artifacts in '{jobname}[{build_no}]"
    )
    return artifacts


def search_artifacts(
    jenkinsurl: str,
    jobname: str,
    artifact_ids=None,
    username: str = "",
    password: str = "",
    ssl_verify: bool = True,
):
    """
    Search the entire history of a jenkins job for a list of artifact names.
    If same_build is true then ensure that all artifacts come from the
    same build of the job
    """
    if not artifact_ids:
        return []

    jenkinsci = Jenkins(
        jenkinsurl, username=username, password=password, ssl_verify=ssl_verify
    )
    job = jenkinsci[jobname]
    build_ids = job.get_build_ids()
    missing_artifacts = set()
    for build_id in build_ids:
        build = job.get_build(build_id)
        artifacts = build.get_artifact_dict()
        if set(artifact_ids).issubset(set(artifacts.keys())):
            return dict((a, artifacts[a]) for a in artifact_ids)
        missing_artifacts = set(artifact_ids) - set(artifacts.keys())
        log.debug(
            msg="Artifacts %s missing from %s #%i"
            % (", ".join(missing_artifacts), jobname, build_id)
        )

    raise ArtifactsMissing(missing_artifacts)


def grab_artifact(
    jenkinsurl: str,
    jobname: str,
    artifactid,
    targetdir: str,
    username: str = "",
    password: str = "",
    strict_validation: bool = True,
    ssl_verify: bool = True,
) -> None:
    """
    Convenience method to find the latest good version of an artifact and
    save it to a target directory.
    Directory is made automatically if not exists.
    """
    artifacts = get_artifacts(
        jenkinsurl,
        jobname,
        artifactid,
        username=username,
        password=password,
        ssl_verify=ssl_verify,
    )
    artifact = artifacts[artifactid]
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)
    artifact.save_to_dir(targetdir, strict_validation)


def block_until_complete(
    jenkinsurl: str,
    jobs: List[str],
    maxwait: int = 12000,
    interval: int = 30,
    raise_on_timeout: bool = True,
    username: str = "",
    password: str = "",
    ssl_verify: bool = True,
) -> None:
    """
    Wait until all of the jobs in the list are complete.
    """
    assert maxwait > 0
    assert maxwait > interval
    assert interval > 0

    report: str = ""
    obj_jenkins: Jenkins = Jenkins(
        jenkinsurl, username=username, password=password, ssl_verify=ssl_verify
    )
    obj_jobs: List[Job] = [obj_jenkins[jid] for jid in jobs]
    for time_left in range(maxwait, 0, -interval):
        still_running = [j for j in obj_jobs if j.is_queued_or_running()]
        if not still_running:
            return
        report = ", ".join('"%s"' % str(a) for a in still_running)
        log.warning(
            "Waiting for jobs %s to complete. Will wait another %is",
            report,
            time_left,
        )
        time.sleep(interval)
    if raise_on_timeout:
        # noinspection PyUnboundLocalVariable
        raise TimeOut(
            "Waited too long for these jobs to complete: %s" % report
        )


def get_view_from_url(
    url: str, username: str = "", password: str = "", ssl_verify: bool = True
) -> View:
    """
    Factory method
    """
    matched = constants.RE_SPLIT_VIEW_URL.search(url)
    if not matched:
        raise BadURL("Cannot parse URL %s" % url)
    jenkinsurl, view_name = matched.groups()
    jenkinsci = Jenkins(
        jenkinsurl, username=username, password=password, ssl_verify=ssl_verify
    )
    return jenkinsci.views[view_name]


def get_nested_view_from_url(
    url: str, username: str = "", password: str = "", ssl_verify: bool = True
) -> View:
    """
    Returns View based on provided URL. Convenient for nested views.
    """
    matched = constants.RE_SPLIT_VIEW_URL.search(url)
    if not matched:
        raise BadURL("Cannot parse URL %s" % url)
    jenkinsci = Jenkins(
        matched.group(0),
        username=username,
        password=password,
        ssl_verify=ssl_verify,
    )
    return jenkinsci.get_view_by_url(url)


def install_artifacts(
    artifacts,
    dirstruct: Dict[str, str],
    installdir: str,
    basestaticurl: str,
    strict_validation: bool = False,
):
    """
    Install the artifacts.
    """
    assert basestaticurl.endswith("/"), "Basestaticurl should end with /"
    installed = []
    for reldir, artifactnames in dirstruct.items():
        destdir = os.path.join(installdir, reldir)
        if not os.path.exists(destdir):
            log.warning("Making install directory %s", destdir)
            os.makedirs(destdir)
        else:
            assert os.path.isdir(destdir)
        for artifactname in artifactnames:
            destpath = os.path.abspath(os.path.join(destdir, artifactname))
            if artifactname in artifacts.keys():
                # The artifact must be loaded from jenkins
                theartifact = artifacts[artifactname]
            else:
                # It's probably a static file,
                # we can get it from the static collection
                staticurl = urlparse.urljoin(basestaticurl, artifactname)
                theartifact = Artifact(artifactname, staticurl, None)
            theartifact.save(destpath, strict_validation)
            installed.append(destpath)
    return installed


def search_artifact_by_regexp(
    jenkinsurl: str,
    jobname: str,
    artifactRegExp: re.Pattern,
    username: str = "",
    password: str = "",
    ssl_verify: bool = True,
) -> Artifact:
    """
    Search the entire history of a Jenkins job for a build which has an
    artifact whose name matches a supplied regular expression.
    Return only that artifact.

    @param jenkinsurl: The base URL of the jenkins server
    @param jobid: The name of the job we are to search through
    @param artifactRegExp: A compiled regular expression object
        (not a re-string)
    @param username: Jenkins login user name, optional
    @param password: Jenkins login password, optional
    """
    job = Jenkins(
        jenkinsurl, username=username, password=password, ssl_verify=ssl_verify
    )
    j = job[jobname]

    build_ids = j.get_build_ids()

    for build_id in build_ids:
        build = j.get_build(build_id)

        artifacts = build.get_artifact_dict()
        for name, art in artifacts.items():
            md_match = artifactRegExp.search(name)

            if md_match:
                return art

    raise ArtifactsMissing()
