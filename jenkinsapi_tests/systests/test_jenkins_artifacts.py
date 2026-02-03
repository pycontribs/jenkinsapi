"""
System tests for `jenkinsapi.jenkins` module.
"""

import os
from posixpath import join
import re
import time
import gzip
import shutil
import tempfile
import logging
from jenkinsapi_tests.systests.job_configs import JOB_WITH_ARTIFACTS
from jenkinsapi_tests.test_utils.random_strings import random_string

log = logging.getLogger(__name__)


def test_artifacts(jenkins):
    job_name = "create_%s" % random_string()
    job = jenkins.create_job(job_name, JOB_WITH_ARTIFACTS)
    job.invoke(block=True)

    build = job.get_last_build()

    while build.is_running():
        time.sleep(1)

    artifacts = build.get_artifact_dict()
    assert isinstance(artifacts, dict) is True

    text_artifact = artifacts["out.txt"]
    binary_artifact = artifacts["out.gz"]

    tempDir = tempfile.mkdtemp()

    try:
        # Verify that we can handle text artifacts
        text_artifact.save_to_dir(tempDir, strict_validation=True)
        text_file_path = join(tempDir, text_artifact.filename)
        assert os.path.exists(text_file_path)
        with open(text_file_path, "rb") as f:
            read_back_text = f.read().strip()
            read_back_text = read_back_text.decode("ascii")
            log.info("Text artifact: %s", read_back_text)
            assert (
                re.match(r"^PING \S+ \(127.0.0.1\)", read_back_text)
                is not None
            )
            assert read_back_text.endswith("ms") is True

        # Verify that we can hande binary artifacts
        binary_artifact.save_to_dir(tempDir, strict_validation=True)
        bin_file_path = join(tempDir, binary_artifact.filename)
        assert os.path.exists(bin_file_path)
        with gzip.open(bin_file_path, "rb") as f:
            read_back_text = f.read().strip()
            read_back_text = read_back_text.decode("ascii")
            assert (
                re.match(r"^PING \S+ \(127.0.0.1\)", read_back_text)
                is not None
            )
            assert read_back_text.endswith("ms") is True
    finally:
        shutil.rmtree(tempDir)
