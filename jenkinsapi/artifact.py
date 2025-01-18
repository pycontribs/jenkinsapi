"""
Artifacts can be used to represent data created as a side-effect of running
a Jenkins build.

Artifacts are files which are associated with a single build. A build can
have any number of artifacts associated with it.

This module provides a class called Artifact which allows you to download
objects from the server and also access them as a stream.
"""

from __future__ import annotations

import os
import logging
import hashlib
from typing import Any, Literal

from jenkinsapi.fingerprint import Fingerprint
from jenkinsapi.custom_exceptions import ArtifactBroken

log = logging.getLogger(__name__)


class Artifact(object):
    """
    Represents a single Jenkins artifact, usually some kind of file
    generated as a by-product of executing a Jenkins build.
    """

    def __init__(
        self,
        filename: str,
        url: str,
        build: "Build",
        relative_path: str | None = None,
    ) -> None:
        self.filename: str = filename
        self.url: str = url
        self.build: "Build" = build
        self.relative_path: str | None = relative_path

    def save(self, fspath: str, strict_validation: bool = False) -> str:
        """
        Save the artifact to an explicit path. The containing directory must
        exist. Returns a reference to the file which has just been writen to.

        :param fspath: full pathname including the filename, str
        :return: filepath
        """
        log.info(msg="Saving artifact @ %s to %s" % (self.url, fspath))
        if not fspath.endswith(self.filename):
            log.warning(
                "Attempt to change the filename of artifact %s on save.",
                self.filename,
            )
        if os.path.exists(fspath):
            if self.build:
                try:
                    if self._verify_download(fspath, strict_validation):
                        log.info(
                            "Local copy of %s is already up to date.",
                            self.filename,
                        )
                        return fspath
                except ArtifactBroken:
                    log.warning("Jenkins artifact could not be identified.")
            else:
                log.info(
                    "This file did not originate from Jenkins, "
                    "so cannot check."
                )
        else:
            log.info("Local file is missing, downloading new.")
        filepath = self._do_download(fspath)
        self._verify_download(filepath, strict_validation)
        return fspath

    def get_jenkins_obj(self) -> Jenkins:
        return self.build.get_jenkins_obj()

    def get_data(self) -> Any:
        """
        Grab the text of the artifact
        """
        response = self.get_jenkins_obj().requester.get_and_confirm_status(
            self.url
        )
        return response.content

    def _do_download(self, fspath: str) -> str:
        """
        Download the the artifact to a path.
        """
        data = self.get_jenkins_obj().requester.get_and_confirm_status(
            self.url, stream=True
        )
        with open(fspath, "wb") as out:
            for chunk in data.iter_content(chunk_size=1024):
                out.write(chunk)
        return fspath

    def _verify_download(self, fspath, strict_validation) -> Literal[True]:
        """
        Verify that a downloaded object has a valid fingerprint.

        Returns True if the fingerprint is valid, raises an exception if
        the fingerprint is invalid.
        """
        local_md5 = self._md5sum(fspath)
        baseurl = self.build.job.jenkins.baseurl
        fp = Fingerprint(baseurl, local_md5, self.build.job.jenkins)
        valid = fp.validate_for_build(
            self.filename, self.build.job.get_full_name(), self.build.buildno
        )
        if not valid or (fp.unknown and strict_validation):
            # strict = 404 as invalid
            raise ArtifactBroken(
                "Artifact %s seems to be broken, check %s"
                % (local_md5, baseurl)
            )
        return True

    def _md5sum(self, fspath: str, chunksize: int = 2**20) -> str:
        """
        A MD5 hashing function intended to produce the same results as that
        used by Jenkins.
        """
        md5 = hashlib.md5()
        with open(fspath, "rb") as f:
            for chunk in iter(lambda: f.read(chunksize), ""):
                if chunk:
                    md5.update(chunk)
                else:
                    break
        return md5.hexdigest()

    def save_to_dir(
        self, dirpath: str, strict_validation: bool = False
    ) -> str:
        """
        Save the artifact to a folder. The containing directory must exist,
        but use the artifact's default filename.
        """
        assert os.path.exists(dirpath)
        assert os.path.isdir(dirpath)
        outputfilepath: str = os.path.join(dirpath, self.filename)
        return self.save(outputfilepath, strict_validation)

    def __repr__(self) -> str:
        """
        Produce a handy repr-string.
        """
        return """<%s.%s %s>""" % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.url,
        )
