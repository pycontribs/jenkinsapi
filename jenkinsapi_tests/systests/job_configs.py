"""
A selection of job objects used in testing.
"""

EMPTY_JOB = """\
<?xml version="1.0" encoding="UTF-8"?><project>
  <actions/>
  <description/>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>
""".strip()

LONG_RUNNING_JOB = """
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>sleep 100</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>""".strip()

SHORTISH_JOB = """
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>ping -c 5 127.0.0.1</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>""".strip()


SCM_GIT_JOB = """
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.plugins.git.GitSCM">
    <configVersion>2</configVersion>
    <userRemoteConfigs>
      <hudson.plugins.git.UserRemoteConfig>
        <name></name>
        <refspec></refspec>
        <url>https://github.com/salimfadhley/jenkinsapi.git</url>
      </hudson.plugins.git.UserRemoteConfig>
    </userRemoteConfigs>
    <branches>
      <hudson.plugins.git.BranchSpec>
        <name>**</name>
      </hudson.plugins.git.BranchSpec>
    </branches>
    <disableSubmodules>false</disableSubmodules>
    <recursiveSubmodules>false</recursiveSubmodules>
    <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
    <authorOrCommitter>false</authorOrCommitter>
    <clean>false</clean>
    <wipeOutWorkspace>false</wipeOutWorkspace>
    <pruneBranches>false</pruneBranches>
    <remotePoll>false</remotePoll>
    <ignoreNotifyCommit>false</ignoreNotifyCommit>
    <useShallowClone>false</useShallowClone>
    <buildChooser class="hudson.plugins.git.util.DefaultBuildChooser"/>
    <gitTool>Default</gitTool>
    <submoduleCfg class="list"/>
    <relativeTargetDir></relativeTargetDir>
    <reference></reference>
    <excludedRegions></excludedRegions>
    <excludedUsers></excludedUsers>
    <gitConfigName></gitConfigName>
    <gitConfigEmail></gitConfigEmail>
    <skipTag>true</skipTag>
    <includedRegions></includedRegions>
    <scmName></scmName>
  </scm>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>""".strip()

JOB_WITH_ARTIFACTS = """
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description>Ping a load of stuff for about 10s</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>ping -c 10 127.0.0.1 > out.txt
gzip &lt; out.txt &gt; out.gz</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers>
    <hudson.tasks.ArtifactArchiver>
      <artifacts>*.txt,*.gz</artifacts>
      <latestOnly>false</latestOnly>
    </hudson.tasks.ArtifactArchiver>
    <hudson.tasks.Fingerprinter>
      <targets>*.*</targets>
      <recordBuildArtifacts>true</recordBuildArtifacts>
    </hudson.tasks.Fingerprinter>
  </publishers>
  <buildWrappers/>
</project>""".strip()

MATRIX_JOB = """
<?xml version='1.0' encoding='UTF-8'?>
<matrix-project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <axes>
    <hudson.matrix.TextAxis>
      <name>foo</name>
      <values>
        <string>one</string>
        <string>two</string>
        <string>three</string>
      </values>
    </hudson.matrix.TextAxis>
  </axes>
  <builders>
    <hudson.tasks.Shell>
      <command>ping -c 10 127.0.0.1</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</matrix-project>""".strip()

JOB_WITH_FILE = """
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.FileParameterDefinition>
          <name>file.txt</name>
          <description></description>
        </hudson.model.FileParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>cat file.txt</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers>
    <hudson.tasks.ArtifactArchiver>
      <artifacts>*</artifacts>
      <latestOnly>false</latestOnly>
    </hudson.tasks.ArtifactArchiver>
  </publishers>
  <buildWrappers/>
</project>""".strip()

JOB_WITH_PARAMETERS = """
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description>A build that explores the wonderous possibilities of parameterized builds.</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>B</name>
          <description>B, like buzzing B.</description>
          <defaultValue></defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>ping -c 1 127.0.0.1 | tee out.txt
echo $A &gt; a.txt
echo $B &gt; b.txt</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers>
    <hudson.tasks.ArtifactArchiver>
      <artifacts>*</artifacts>
      <latestOnly>false</latestOnly>
    </hudson.tasks.ArtifactArchiver>
    <hudson.tasks.Fingerprinter>
      <targets></targets>
      <recordBuildArtifacts>true</recordBuildArtifacts>
    </hudson.tasks.Fingerprinter>
  </publishers>
  <buildWrappers/>
</project>""".strip()  # noqa

JOB_WITH_FILE_AND_PARAMS = """
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.FileParameterDefinition>
          <name>file.txt</name>
          <description></description>
        </hudson.model.FileParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>B</name>
          <description>B, like buzzing B.</description>
          <defaultValue></defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>cat file.txt;echo $B &gt; file1.txt</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers>
    <hudson.tasks.ArtifactArchiver>
      <artifacts>*</artifacts>
      <latestOnly>false</latestOnly>
    </hudson.tasks.ArtifactArchiver>
  </publishers>
  <buildWrappers/>
</project>""".strip()

JOB_WITH_ENV_VARS = """\
<?xml version="1.0" encoding="UTF-8"?><project>
  <actions/>
  <description/>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers>
    <EnvInjectBuildWrapper plugin="envinject@1.93.1">
      <info>
        <groovyScriptContent>
          return [\'key1\': \'value1\', \'key2\': \'value2\']
        </groovyScriptContent>
        <loadFilesFromMaster>false</loadFilesFromMaster>
      </info>
    </EnvInjectBuildWrapper>
  </buildWrappers>
</project>
""".strip()

PIPELINE_SCM_JOB = """
<?xml version='1.0' encoding='UTF-8'?>
<flow-definition>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition">
    <scm class="hudson.plugins.git.GitSCM">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>https://github.com/salimfadhley/jenkinsapi.git</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>main</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
    </scm>
  </definition>
</flow-definition>""".strip()

MULTIBRANCH_GIT_SCM_JOB = """
<?xml version='1.0' encoding='UTF-8'?>
<org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject plugin="workflow-multibranch@821.vc3b_4ea_780798">
<actions/>
<description/>
<properties/>
<folderViews class="jenkins.branch.MultiBranchProjectViewHolder" plugin="branch-api@2.1259.v45c101731c76">
<owner class="org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject" reference="../.."/>
</folderViews>
<healthMetrics/>
<icon class="jenkins.branch.MetadataActionFolderIcon" plugin="branch-api@2.1259.v45c101731c76">
<owner class="org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject" reference="../.."/>
</icon>
<orphanedItemStrategy class="com.cloudbees.hudson.plugins.folder.computed.DefaultOrphanedItemStrategy" plugin="cloudbees-folder@6.1073.va_7888eb_dd514">
<pruneDeadBranches>true</pruneDeadBranches>
<daysToKeep>-1</daysToKeep>
<numToKeep>-1</numToKeep>
<abortBuilds>false</abortBuilds>
</orphanedItemStrategy>
<triggers/>
<disabled>false</disabled>
<sources class="jenkins.branch.MultiBranchProject$BranchSourceList" plugin="branch-api@2.1259.v45c101731c76">
<data>
<jenkins.branch.BranchSource>
<source class="jenkins.plugins.git.GitSCMSource" plugin="git@5.8.0">
<id>e0a4ce06-e537-4893-9ba4-2dd4f18d7a44</id>
<remote>https://github.com/pycontribs/jenkinsapi</remote>
<credentialsId/>
<traits>
<jenkins.plugins.git.traits.BranchDiscoveryTrait/>
<jenkins.scm.impl.trait.RegexSCMHeadFilterTrait plugin="scm-api@712.v8846fdd68c88">
<regex>(master.*)</regex>
</jenkins.scm.impl.trait.RegexSCMHeadFilterTrait>
</traits>
</source>
<strategy class="jenkins.branch.DefaultBranchPropertyStrategy">
<properties class="empty-list"/>
</strategy>
</jenkins.branch.BranchSource>
</data>
<owner class="org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject" reference="../.."/>
</sources>
<factory class="org.jenkinsci.plugins.workflow.multibranch.WorkflowBranchProjectFactory">
<owner class="org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject" reference="../.."/>
<scriptPath>uv.lock</scriptPath>
</factory>
</org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject>
""".strip()

MULTIBRANCH_GIT_BRANCH_JOB_PROPERTY = """
<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@1559.va_a_533730b_ea_d">
<actions/>
<keepDependencies>false</keepDependencies>
<properties>
<org.jenkinsci.plugins.workflow.multibranch.BranchJobProperty plugin="workflow-multibranch@821.vc3b_4ea_780798">
<branch plugin="branch-api@2.1259.v45c101731c76">
<sourceId>bc1f7bd0-b8d0-48db-ac98-bcae92939715</sourceId>
<head plugin="scm-api@712.v8846fdd68c88">
<name>a</name>
</head>
<scm class="hudson.plugins.git.GitSCM" plugin="git@5.8.0">
<configVersion>2</configVersion>
<userRemoteConfigs>
<hudson.plugins.git.UserRemoteConfig>
<url>https://github.com/pycontribs/jenkinsapi.git</url>
</hudson.plugins.git.UserRemoteConfig>
</userRemoteConfigs>
<branches>
<hudson.plugins.git.BranchSpec>
<name>*/master</name>
</hudson.plugins.git.BranchSpec>
</branches>
<doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
<submoduleCfg class="empty-list"/>
<extensions/>
</scm>
<properties/>
<actions/>
</branch>
</org.jenkinsci.plugins.workflow.multibranch.BranchJobProperty>
</properties>
<definition class="org.jenkinsci.plugins.workflow.multibranch.SCMBinder" plugin="workflow-multibranch@821.vc3b_4ea_780798">
<scriptPath>uv.lock</scriptPath>
</definition>
<triggers/>
<disabled>false</disabled>
</flow-definition>
""".strip()

MULTIBRANCH_GITHUB_SCM_JOB = """
<?xml version='1.0' encoding='UTF-8'?>
<org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject plugin="workflow-multibranch@821.vc3b_4ea_780798">
<actions/>
<description/>
<properties/>
<folderViews class="jenkins.branch.MultiBranchProjectViewHolder" plugin="branch-api@2.1259.v45c101731c76">
<owner class="org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject" reference="../.."/>
</folderViews>
<healthMetrics/>
<icon class="jenkins.branch.MetadataActionFolderIcon" plugin="branch-api@2.1259.v45c101731c76">
<owner class="org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject" reference="../.."/>
</icon>
<orphanedItemStrategy class="com.cloudbees.hudson.plugins.folder.computed.DefaultOrphanedItemStrategy" plugin="cloudbees-folder@6.1073.va_7888eb_dd514">
<pruneDeadBranches>true</pruneDeadBranches>
<daysToKeep>-1</daysToKeep>
<numToKeep>-1</numToKeep>
<abortBuilds>false</abortBuilds>
</orphanedItemStrategy>
<triggers/>
<disabled>false</disabled>
<sources class="jenkins.branch.MultiBranchProject$BranchSourceList" plugin="branch-api@2.1259.v45c101731c76">
<data>
<jenkins.branch.BranchSource>
<source class="org.jenkinsci.plugins.github_branch_source.GitHubSCMSource" plugin="github-branch-source@1917.v9ee8a_39b_3d0d">
<id>e82f0840-83c9-44b3-a903-3825f776da38</id>
<apiUri>https://api.github.com</apiUri>
<repoOwner>pycontribs</repoOwner>
<repository>jenkinsapi</repository>
<repositoryUrl>https://github.com/pycontribs/jenkinsapi</repositoryUrl>
<traits>
<org.jenkinsci.plugins.github__branch__source.BranchDiscoveryTrait>
<strategyId>1</strategyId>
</org.jenkinsci.plugins.github__branch__source.BranchDiscoveryTrait>
<org.jenkinsci.plugins.github__branch__source.OriginPullRequestDiscoveryTrait>
<strategyId>2</strategyId>
</org.jenkinsci.plugins.github__branch__source.OriginPullRequestDiscoveryTrait>
<org.jenkinsci.plugins.github__branch__source.ForkPullRequestDiscoveryTrait>
<strategyId>2</strategyId>
<trust class="org.jenkinsci.plugins.github_branch_source.ForkPullRequestDiscoveryTrait$TrustPermission"/>
</org.jenkinsci.plugins.github__branch__source.ForkPullRequestDiscoveryTrait>
</traits>
</source>
<strategy class="jenkins.branch.DefaultBranchPropertyStrategy">
<properties class="empty-list"/>
</strategy>
</jenkins.branch.BranchSource>
</data>
<owner class="org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject" reference="../.."/>
</sources>
<factory class="org.jenkinsci.plugins.workflow.multibranch.WorkflowBranchProjectFactory">
<owner class="org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject" reference="../.."/>
<scriptPath>uv.lock</scriptPath>
</factory>
</org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject>
"""
