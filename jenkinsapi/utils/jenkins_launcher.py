import os
import time
import shutil
import logging
import datetime
import tempfile
import posixpath
import requests
import queue
import threading
import tarfile
import subprocess
from urllib3 import Retry
from urllib.parse import urlparse

from requests.adapters import HTTPAdapter

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.custom_exceptions import JenkinsAPIException

log = logging.getLogger(__name__)


class FailedToStart(Exception):
    pass


class TimeOut(Exception):
    pass


class StreamThread(threading.Thread):
    def __init__(self, name, q, stream, fn_log):
        threading.Thread.__init__(self)
        self.name = name
        self.queue = q
        self.stream = stream
        self.fn_log = fn_log
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        log.info("Starting %s", self.name)

        while True:
            if self._stop.is_set():
                break
            line = self.stream.readline()
            if line:
                self.fn_log(line.rstrip())
                self.queue.put((self.name, line))
            else:
                break

        self.queue.put((self.name, None))


class JenkinsLancher(object):
    """
    Launch jenkins
    """

    JENKINS_WEEKLY_WAR_URL = "http://get.jenkins.io/war/latest/jenkins.war"
    JENKINS_LTS_WAR_URL = (
        "https://get.jenkins.io/war-stable/latest/jenkins.war"
    )

    def __init__(
        self,
        local_orig_dir,
        systests_dir,
        war_name,
        plugin_urls=None,
        jenkins_url=None,
    ):
        if jenkins_url is not None:
            self.jenkins_url = jenkins_url
            self.http_port = urlparse(jenkins_url).port
            self.start_new_instance = False
        else:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("", 0))
            sock.listen(1)
            port = sock.getsockname()[1]
            sock.close()
            self.http_port = port
            self.jenkins_url = "http://localhost:%s" % self.http_port
            self.start_new_instance = True

        self.threads = []
        self.war_path = os.path.join(local_orig_dir, war_name)
        self.local_orig_dir = local_orig_dir
        self.systests_dir = systests_dir
        self.war_filename = war_name

        if "JENKINS_HOME" not in os.environ:
            self.jenkins_home = tempfile.mkdtemp(prefix="jenkins-home-")
            os.environ["JENKINS_HOME"] = self.jenkins_home
        else:
            self.jenkins_home = os.environ["JENKINS_HOME"]

        self.jenkins_process = None
        self.queue = queue.Queue()
        self.plugin_urls = plugin_urls or []
        if os.environ.get("JENKINS_VERSION", "stable") == "stable":
            self.JENKINS_WAR_URL = self.JENKINS_LTS_WAR_URL
        else:
            self.JENKINS_WAR_URL = self.JENKINS_WEEKLY_WAR_URL

    def update_war(self):
        os.chdir(self.systests_dir)
        if os.path.exists(self.war_path):
            log.info(
                "War file already present, delete it to redownload and"
                " update jenkins"
            )
        else:
            log.info("Downloading Jenkins War")
            script_dir = os.path.join(self.systests_dir, "get-jenkins-war.sh")
            subprocess.check_call(
                [
                    script_dir,
                    self.JENKINS_WAR_URL,
                    self.local_orig_dir,
                    self.war_filename,
                ]
            )

    def update_config(self):
        from jenkinsapi_tests import systests

        file = os.path.join(
            os.path.dirname(systests.__file__), "jenkins_home.tar.gz"
        )

        with open(file, "rb") as f:
            with tarfile.open(fileobj=f, mode="r:gz") as tarball:
                tarball.extractall(path=self.jenkins_home)

    def install_plugins(self):
        plugin_dest_dir = os.path.join(self.jenkins_home, "plugins")
        log.info("Plugins will be installed in '%s'", plugin_dest_dir)

        if not os.path.exists(plugin_dest_dir):
            os.mkdir(plugin_dest_dir)

        for url in self.plugin_urls:
            self.install_plugin(url, plugin_dest_dir)

    def install_plugin(self, hpi_url, plugin_dest_dir):
        sess = requests.Session()
        adapter = HTTPAdapter(
            max_retries=Retry(total=5, backoff_factor=1, allowed_methods=None)
        )
        sess.mount("http://", adapter)
        sess.mount("https://", adapter)

        path = urlparse(hpi_url).path
        filename = posixpath.basename(path)
        plugin_orig_dir = os.path.join(self.local_orig_dir, "plugins")
        if not os.path.exists(plugin_orig_dir):
            os.mkdir(plugin_orig_dir)
        plugin_orig_path = os.path.join(plugin_orig_dir, filename)
        plugin_dest_path = os.path.join(plugin_dest_dir, filename)
        if os.path.exists(plugin_orig_path):
            log.info(
                "%s already locally present, delete the file to redownload"
                " and update",
                filename,
            )
        else:
            log.info("Downloading %s from %s", filename, hpi_url)
            with sess.get(hpi_url, stream=True) as hget:
                hget.raise_for_status()
                with open(plugin_orig_path, "wb") as hpi:
                    for chunk in hget.iter_content(chunk_size=8192):
                        hpi.write(chunk)
        log.info("Installing %s", filename)
        shutil.copy(plugin_orig_path, plugin_dest_path)
        # Create an empty .pinned file, so that the downloaded plugin
        # will be used, instead of the version bundled in jenkins.war
        # See https://wiki.jenkins-ci.org/display/JENKINS/Pinned+Plugins
        open(plugin_dest_path + ".pinned", "a").close()

    def stop(self):
        if self.start_new_instance:
            log.info("Shutting down jenkins.")
            # Start the threads
            for thread in self.threads:
                thread.stop()

            Jenkins(self.jenkins_url).shutdown()
            # self.jenkins_process.terminate()
            # self.jenkins_process.wait()
            # Do not remove jenkins home if JENKINS_URL is set
            if "JENKINS_URL" not in os.environ:
                shutil.rmtree(self.jenkins_home, ignore_errors=True)
            log.info("Jenkins stopped.")

    def block_until_jenkins_ready(self, timeout):
        start_time = datetime.datetime.now()
        timeout_time = start_time + datetime.timedelta(seconds=timeout)

        while True:
            try:
                Jenkins(self.jenkins_url)
                log.info("Jenkins is finally ready for use.")
            except JenkinsAPIException:
                log.info("Jenkins is not yet ready...")
            if datetime.datetime.now() > timeout_time:
                raise TimeOut("Took too long for Jenkins to become ready...")
            time.sleep(5)

    def start(self, timeout=60):
        if self.start_new_instance:
            self.jenkins_home = os.environ.get(
                "JENKINS_HOME", self.jenkins_home
            )
            self.update_war()
            self.update_config()
            self.install_plugins()

            os.chdir(self.local_orig_dir)

            jenkins_command = [
                "java",
                "-Djenkins.install.runSetupWizard=false",
                "-Dhudson.DNSMultiCast.disabled=true",
                "-jar",
                self.war_filename,
                "--httpPort=%d" % self.http_port,
            ]

            log.info("About to start Jenkins...")
            log.info("%s> %s", os.getcwd(), " ".join(jenkins_command))
            self.jenkins_process = subprocess.Popen(
                jenkins_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.threads = [
                StreamThread(
                    "out", self.queue, self.jenkins_process.stdout, log.info
                ),
                StreamThread(
                    "err", self.queue, self.jenkins_process.stderr, log.warning
                ),
            ]

            # Start the threads
            for thread in self.threads:
                thread.start()

            while True:
                try:
                    streamName, line = self.queue.get(
                        block=True, timeout=timeout
                    )
                    # Python 3.x
                    if isinstance(line, bytes):
                        line = line.decode("UTF-8")
                except queue.Empty:
                    log.warning("Input ended unexpectedly")
                    break
                else:
                    if line:
                        if "Failed to initialize Jenkins" in line:
                            raise FailedToStart(line)

                        if "Invalid or corrupt jarfile" in line:
                            raise FailedToStart(line)

                        if "is fully up and running" in line:
                            log.info(line)
                            return
                    else:
                        log.warning("Stream %s has terminated", streamName)

            self.block_until_jenkins_ready(timeout)


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.INFO)

    log.info("Hello!")

    jl = JenkinsLancher(
        "/home/aleksey/src/jenkinsapi_lechat/jenkinsapi_tests"
        "/systests/localinstance_files",
        "/home/aleksey/src/jenkinsapi_lechat/jenkinsapi_tests/systests",
        "jenkins.war",
    )

    jl.start()
    log.info("Jenkins was launched...")

    time.sleep(10)

    log.info("...now to shut it down!")
    jl.stop()
