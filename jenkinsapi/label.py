from jenkinsapi.jenkinsbase import JenkinsBase

class Label(JenkinsBase):
    def __init__(self, name, jenkins_obj):
        self.name = name
        self.jenkins = jenkins_obj
        self.baseurl = self.jenkins.baseurl + "/label/" + self.name
        self._nodes = None
        self._jobs = None
        JenkinsBase.__init__(self, self.baseurl)

    def __str__(self):
        return self.name

    def get_jenkins_obj(self):
        return self.jenkins

    @property
    def description(self):
        return self._data['description']

    @property
    def nodes(self):
        if not self._nodes:
            self._get_nodes()

        return self._nodes

    def _get_nodes(self):
        self._nodes = []
        for node in self._data['nodes']:
            self._nodes.append(node['nodeName'])

    @property
    def jobs(self):
        if not self._jobs:
            self._get_jobs()
        return self._jobs

    def _get_jobs(self):
        self._jobs = []
        for job in self._data['tiedJobs']:
            self._jobs.append(job['name'])
