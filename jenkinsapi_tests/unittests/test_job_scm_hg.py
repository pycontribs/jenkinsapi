# flake8: noqa
#    import mock
#
#    import unittest
#
#    from jenkinsapi import config
#    from jenkinsapi.job import Job
#    from jenkinsapi.jenkinsbase import JenkinsBase
#
#
#    CFG_NODE = """
#    <project>
#    <scm class="hudson.plugins.mercurial.MercurialSCM" plugin="mercurial@1.42">
#    <source>http://cm5/hg/sandbox/v01.0/int</source>
#    <modules/>
#    <clean>false</clean>
#    <browser class="hudson.plugins.mercurial.browser.HgWeb">
#    <url>http://cm5/hg/sandbox/v01.0/int/</url>
#    </browser>
#    </scm>
#    </project>
#    """
#
#    # TODO: Make JOB_DATA to be one coming from Hg job
#    class TestHgJob(unittest.TestCase):
#        JOB_DATA = {
#            "actions": [],
#            "description": "test job",
#            "displayName": "foo",
#            "displayNameOrNull": None,
#            "name": "foo",
#            "url": "http://halob:8080/job/foo/",
#            "buildable": True,
#            "builds": [
#                {"number": 3, "url": "http://halob:8080/job/foo/3/"},
#                {"number": 2, "url": "http://halob:8080/job/foo/2/"},
#                {"number": 1, "url": "http://halob:8080/job/foo/1/"},
#            ],
#            "color": "blue",
#            "firstBuild": {"number": 1, "url": "http://halob:8080/job/foo/1/"},
#            "healthReport": [
#                {
#                    "description": "Build stability: No recent builds failed.",
#                    "iconUrl": "health-80plus.png",
#                    "score": 100,
#                }
#            ],
#            "inQueue": False,
#            "keepDependencies": False,
#            # build running
#            "lastBuild": {"number": 4, "url": "http://halob:8080/job/foo/4/"},
#            "lastCompletedBuild": {
#                "number": 3,
#                "url": "http://halob:8080/job/foo/3/",
#            },
#            "lastFailedBuild": None,
#            "lastStableBuild": {
#                "number": 3,
#                "url": "http://halob:8080/job/foo/3/",
#            },
#            "lastSuccessfulBuild": {
#                "number": 3,
#                "url": "http://halob:8080/job/foo/3/",
#            },
#            "lastUnstableBuild": None,
#            "lastUnsuccessfulBuild": None,
#            "nextBuildNumber": 4,
#            "property": [],
#            "queueItem": None,
#            "concurrentBuild": False,
#            "downstreamProjects": [],
#            "scm": {},
#            "upstreamProjects": [],
#        }
#
#        URL_DATA = {"http://halob:8080/job/foo/%s" % config.JENKINS_API: JOB_DATA}
#
#        def fakeGetData(self, url, *args, **kwargs):
#            try:
#                return TestHgJob.URL_DATA[url]
#            except KeyError:
#                raise Exception("Missing data for %s" % url)
#
#        @mock.patch.object(JenkinsBase, "get_data", fakeGetData)
#        def setUp(self):
#            self.J = mock.MagicMock()  # Jenkins object
#            self.j = Job("http://halob:8080/job/foo/", "foo", self.J)
#
#        def configtree_with_branch(self):
#            config_node = CFG_NODE
#            return config_node
#
#        def configtree_with_default_branch(self):
#            config_node = CFG_NODE
#            return config_node
#
#        def configtree_multibranch_git(self):
#            config_node = """
#    <flow-definition plugin="workflow-job@2.35">
#        <keepDependencies>false</keepDependencies>
#        <properties>
#            <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
#                <triggers>
#                    <hudson.triggers.TimerTrigger>
#                        <spec>H H * * H(6-7)</spec>
#                    </hudson.triggers.TimerTrigger>
#                    <jenkins.triggers.ReverseBuildTrigger>
#                        <spec></spec>
#                        <upstreamProjects></upstreamProjects>
#                        <threshold>
#                            <name>SUCCESS</name>
#                            <ordinal>0</ordinal>
#                            <color>BLUE</color>
#                            <completeBuild>true</completeBuild>
#                        </threshold>
#                    </jenkins.triggers.ReverseBuildTrigger>
#                </triggers>
#            </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
#            <jenkins.model.BuildDiscarderProperty>
#                <strategy class="hudson.tasks.LogRotator">
#                    <daysToKeep>-1</daysToKeep>
#                    <numToKeep>5</numToKeep>
#                    <artifactDaysToKeep>-1</artifactDaysToKeep>
#                    <artifactNumToKeep>5</artifactNumToKeep>
#                </strategy>
#            </jenkins.model.BuildDiscarderProperty>
#            <org.jenkinsci.plugins.workflow.multibranch.BranchJobProperty
#                    plugin="workflow-multibranch@2.21">
#                <branch plugin="branch-api@2.5.4">
#                    <sourceId>a2d4bcda-6141-4af2-8088-39139a147902</sourceId>
#                    <head class="com.cloudbees.jenkins.plugins.bitbucket.BranchSCMHead"
#                            plugin="cloudbees-bitbucket-branch-source@2.5.0">
#                        <name>master</name>
#                        <repositoryType>GIT</repositoryType>
#                    </head>
#                    <scm class="hudson.plugins.git.GitSCM" plugin="git@3.12.1">
#                        <configVersion>2</configVersion>
#                        <userRemoteConfigs>
#                            <hudson.plugins.git.UserRemoteConfig>
#                                <name>origin</name>
#                                <refspec>+refs/heads/master:refs/remotes/origin/master</refspec>
#                                <url>ssh://git@bitbucket.site/project-name/reponame.git</url>
#                                <credentialsId>jenkins-stash</credentialsId>
#                            </hudson.plugins.git.UserRemoteConfig>
#                        </userRemoteConfigs>
#                        <branches class="singleton-list">
#                            <hudson.plugins.git.BranchSpec>
#                                <name>master</name>
#                            </hudson.plugins.git.BranchSpec>
#                        </branches>
#                        <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
#                        <browser class="hudson.plugins.git.browser.BitbucketWeb">
#                            <url>https://bitbucket.site/projects/project-name/repos/reponame</url>
#                        </browser>
#                        <submoduleCfg class="empty-list"/>
#                        <extensions>
#                            <jenkins.plugins.git.GitSCMSourceDefaults>
#                                <includeTags>false</includeTags>
#                            </jenkins.plugins.git.GitSCMSourceDefaults>
#                        </extensions>
#                    </scm>
#                    <properties/>
#                </branch>
#            </org.jenkinsci.plugins.workflow.multibranch.BranchJobProperty>
#        </properties>
#        <definition class="org.jenkinsci.plugins.workflow.multibranch.SCMBinder"
#                plugin="workflow-multibranch@2.21">
#            <scriptPath>Jenkinsfile</scriptPath>
#        </definition>
#        <triggers/>
#        <disabled>false</disabled>
#    </flow-definition>
#            """
#            return config_node
#
#        @mock.patch.object(Job, "get_config", configtree_with_branch)
#        def test_hg_attributes(self):
#            expected_url = ["http://cm5/hg/sandbox/v01.0/int"]
#            self.j.load_config()
#            self.assertEqual(self.j.get_scm_type(), "hg")
#            self.assertEqual(self.j.get_scm_url(), expected_url)
#            self.assertEqual(self.j.get_scm_branch(), ["testme"])
#
#        @mock.patch.object(Job, "get_config", configtree_with_default_branch)
#        def test_hg_attributes_default_branch(self):
#            self.j.load_config()
#            self.assertEqual(self.j.get_scm_branch(), ["default"])
#
#        @mock.patch.object(Job, "get_config", configtree_multibranch_git)
#        def test_git_attributes_multibranch(self):
#            expected_url = ["ssh://git@bitbucket.site/project-name/reponame.git"]
#            self.j.load_config()
#            self.assertEqual(self.j.get_scm_type(), "git")
#            self.assertEqual(self.j.get_scm_url(), expected_url)
#            self.assertEqual(self.j.get_scm_branch(), ["master"])
#
#
#    if __name__ == "__main__":
#        unittest.main()
