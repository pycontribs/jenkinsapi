"""
How to create views
"""

import logging
from pkg_resources import resource_string
from jenkinsapi.jenkins import Jenkins

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

jenkins_url = "http://localhost:8080/"

jenkins = Jenkins(jenkins_url, lazy=True)

# Create ListView in main view
logger.info("Attempting to create new view")
test_view_name = "SimpleListView"

# Views object appears as a dictionary of views
if test_view_name not in jenkins.views:
    new_view = jenkins.views.create(test_view_name)
    if new_view is None:
        logger.error("View %s was not created", test_view_name)
    else:
        logger.info(
            "View %s has been created: %s", new_view.name, new_view.baseurl
        )
else:
    logger.info("View %s already exists", test_view_name)

# No error is raised if view already exists
logger.info("Attempting to create view that already exists")
my_view = jenkins.views.create(test_view_name)

logger.info("Create job and assign it to a view")
job_name = "foo_job2"
xml = resource_string("examples", "addjob.xml")

my_job = jenkins.create_job(jobname=job_name, xml=xml)

# add_job supports two parameters: job_name and job object
# passing job object will remove verification calls to Jenkins
my_view.add_job(job_name, my_job)
assert len(my_view) == 1

logger.info("Attempting to delete view that already exists")
del jenkins.views[test_view_name]

if test_view_name in jenkins.views:
    logger.error("View was not deleted")
else:
    logger.info("View has been deleted")

# No error will be raised when attempting to remove non-existing view
logger.info("Attempting to delete view that does not exist")
del jenkins.views[test_view_name]

# Create CategorizedJobsView
config = """
<org.jenkinsci.plugins.categorizedview.CategorizedJobsView>
  <categorizationCriteria>
    <org.jenkinsci.plugins.categorizedview.GroupingRule>
      <groupRegex>.dev.</groupRegex>
      <namingRule>Development</namingRule>
    </org.jenkinsci.plugins.categorizedview.GroupingRule>
    <org.jenkinsci.plugins.categorizedview.GroupingRule>
      <groupRegex>.hml.</groupRegex>
      <namingRule>Homologation</namingRule>
    </org.jenkinsci.plugins.categorizedview.GroupingRule>
  </categorizationCriteria>
</org.jenkinsci.plugins.categorizedview.CategorizedJobsView>
"""
view = jenkins.views.create(
    "My categorized jobs view", jenkins.views.CATEGORIZED_VIEW, config=config
)
