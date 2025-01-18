"""
jenkinsapi class for invoking Jenkins
"""

import os
import sys
import logging
import optparse
from jenkinsapi import jenkins

log = logging.getLogger(__name__)


class JenkinsInvoke(object):
    """
    JenkinsInvoke object implements class to call from command line
    """

    @classmethod
    def mkparser(cls):
        parser = optparse.OptionParser()
        DEFAULT_BASEURL = os.environ.get(
            "JENKINS_URL", "http://localhost/jenkins"
        )
        parser.help_text = (
            "Execute a number of jenkins jobs on the server of your choice."
            + " Optionally block until the jobs are complete."
        )
        parser.add_option(
            "-J",
            "--jenkinsbase",
            dest="baseurl",
            help="Base URL for the Jenkins server, default is %s"
            % DEFAULT_BASEURL,
            type="str",
            default=DEFAULT_BASEURL,
        )
        parser.add_option(
            "--username",
            "-u",
            dest="username",
            help="Username for jenkins authentification",
            type="str",
            default=None,
        )
        parser.add_option(
            "--password",
            "-p",
            dest="password",
            help="password for jenkins user auth",
            type="str",
            default=None,
        )
        parser.add_option(
            "-b",
            "--block",
            dest="block",
            action="store_true",
            default=False,
            help="Block until each of the jobs is complete.",
        )
        parser.add_option(
            "-t",
            "--token",
            dest="token",
            help="Optional security token.",
            default=None,
        )
        return parser

    @classmethod
    def main(cls):
        parser = cls.mkparser()
        options, args = parser.parse_args()
        try:
            assert args, "Need to specify at least one job name"
        except AssertionError as err:
            log.critical(err.message)
            parser.print_help()
            sys.exit(1)
        invoker = cls(options, args)
        invoker()

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
        assert isinstance(block, bool)
        assert isinstance(jobname, str)
        assert token is None or isinstance(token, str)
        job = self.api.get_job(jobname)
        job.invoke(securitytoken=token, block=block)


def main():
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.INFO)
    JenkinsInvoke.main()
