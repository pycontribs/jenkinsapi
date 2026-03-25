"""
jenkinsapi class for invoking Jenkins
"""

import os
import sys
import logging
import argparse
import getpass

from jenkinsapi import jenkins

log = logging.getLogger(__name__)


class JenkinsInvoke(object):
    """
    JenkinsInvoke object implements class to call from command line
    """

    @classmethod
    def mkparser(cls):
        default_baseurl = os.environ.get(
            "JENKINS_URL", "http://localhost/jenkins"
        )
        default_username = (
            os.environ.get("JENKINS_USERNAME")
            or os.environ.get("JENKINS_USER")
            or None
        )
        default_password = (
            os.environ.get("JENKINS_API_TOKEN")
            or os.environ.get("JENKINS_PASSWORD")
            or None
        )
        parser = argparse.ArgumentParser(
            description=(
                "Execute one or more Jenkins jobs on the selected server."
            )
        )
        parser.add_argument(
            "-J",
            "--jenkinsbase",
            dest="baseurl",
            help=(
                "Base URL for the Jenkins server "
                "(default: %(default)s or $JENKINS_URL)"
            ),
            type=str,
            default=default_baseurl,
        )
        parser.add_argument(
            "-u",
            "--username",
            dest="username",
            help=(
                "Username for Jenkins authentication "
                "(default: $JENKINS_USERNAME or $JENKINS_USER)."
            ),
            type=str,
            default=default_username,
        )
        parser.add_argument(
            "-p",
            "--password",
            dest="password",
            help=(
                "Password or API token for Jenkins authentication "
                "(default: $JENKINS_API_TOKEN or $JENKINS_PASSWORD)."
            ),
            type=str,
            default=default_password,
        )
        parser.add_argument(
            "-b",
            "--block",
            dest="block",
            action="store_true",
            default=False,
            help="Block until each job completes.",
        )
        parser.add_argument(
            "-t",
            "--token",
            dest="token",
            help="Optional per-job security token.",
            default=None,
        )
        parser.add_argument(
            "jobs",
            metavar="job",
            nargs="+",
            help="One or more Jenkins job names to invoke.",
        )
        return parser

    @classmethod
    def main(cls):
        parser = cls.mkparser()
        options = parser.parse_args()
        options = cls.resolve_password(
            options=options,
            is_interactive=sys.stdin.isatty(),
            prompt_password=getpass.getpass,
        )
        if options.username and options.password is None:
            parser.error(
                "Password/API token missing. Use --password, set "
                "JENKINS_API_TOKEN/JENKINS_PASSWORD, or run in an "
                "interactive terminal to be prompted."
            )
        invoker = cls(options, options.jobs)
        invoker()

    @staticmethod
    def resolve_password(options, is_interactive, prompt_password):
        if options.username and options.password is None and is_interactive:
            options.password = prompt_password(
                "Jenkins password or API token: "
            )
        return options

    def __init__(self, options, jobs):
        self.options = options
        self.jobs = jobs
        self.api = self._get_api(
            baseurl=options.baseurl,
            username=options.username,
            password=options.password,
        )

    def _get_api(self, baseurl, username, password):
        return jenkins.Jenkins(baseurl, username, password)

    def __call__(self):
        for job in self.jobs:
            self.invokejob(
                job, block=self.options.block, token=self.options.token
            )

    def invokejob(self, jobname, block, token):
        if not isinstance(jobname, str):
            raise TypeError(
                f"jobname must be str, got {type(jobname).__name__}"
            )
        if not isinstance(block, bool):
            raise TypeError(f"block must be bool, got {type(block).__name__}")
        if token is not None and not isinstance(token, str):
            raise TypeError(
                f"token must be None or str, got {type(token).__name__}"
            )
        job = self.api.get_job(jobname)
        job.invoke(securitytoken=token, block=block)


def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.INFO)
    JenkinsInvoke.main()
