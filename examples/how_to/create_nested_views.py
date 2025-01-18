"""
How to create nested views using NestedViews Jenkins plugin

This example requires NestedViews plugin to be installed in Jenkins
You need to have at least one job in your Jenkins to see views
"""

from __future__ import print_function
import logging
from pkg_resources import resource_string
from jenkinsapi.views import Views
from jenkinsapi.jenkins import Jenkins

log_level = getattr(logging, "DEBUG")
logging.basicConfig(level=log_level)
logger = logging.getLogger()

jenkins_url = "http://127.0.0.1:8080/"
jenkins = Jenkins(jenkins_url)

job_name = "foo_job2"
xml = resource_string("examples", "addjob.xml")
j = jenkins.create_job(jobname=job_name, xml=xml)

# Create ListView in main view
logger.info("Attempting to create new nested view")
top_view = jenkins.views.create("TopView", Views.NESTED_VIEW)
logger.info("top_view is %s", top_view)
if top_view is None:
    logger.error("View was not created")
else:
    logger.info("View has been created")

print("top_view.views=", top_view.views.keys())
logger.info("Attempting to create view inside nested view")
sub_view = top_view.views.create("SubView")
if sub_view is None:
    logger.info("View was not created")
else:
    logger.error("View has been created")

logger.info("Attempting to delete sub_view")
del top_view.views["SubView"]
if "SubView" in top_view.views:
    logger.error("SubView was not deleted")
else:
    logger.info("SubView has been deleted")

# Another way of creating sub view
# This way sub view will have jobs in it
logger.info("Attempting to create view with jobs inside nested view")
top_view.views["SubView"] = job_name
if "SubView" not in top_view.views:
    logger.error("View was not created")
else:
    logger.info("View has been created")

logger.info("Attempting to delete sub_view")
del top_view.views["SubView"]
if "SubView" in top_view.views:
    logger.error("SubView was not deleted")
else:
    logger.info("SubView has been deleted")

logger.info("Attempting to delete top view")
del jenkins.views["TopView"]
if "TopView" not in jenkins.views:
    logger.info("View has been deleted")
else:
    logger.error("View was not deleted")

# Delete job that we created
jenkins.delete_job(job_name)
