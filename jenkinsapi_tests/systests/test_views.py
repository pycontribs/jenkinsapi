"""
System tests for `jenkinsapi.jenkins` module.
"""

import logging
from jenkinsapi.view import View
from jenkinsapi.views import Views
from jenkinsapi.job import Job
from jenkinsapi.api import get_view_from_url
from jenkinsapi_tests.systests.job_configs import EMPTY_JOB
from jenkinsapi_tests.systests.view_configs import VIEW_WITH_FILTER_AND_REGEX
from jenkinsapi_tests.test_utils.random_strings import random_string

log = logging.getLogger(__name__)


def create_job(jenkins, job_name="whatever"):
    job = jenkins.create_job(job_name, EMPTY_JOB)
    return job


def test_make_views(jenkins):
    view_name = random_string()
    assert view_name not in jenkins.views
    new_view = jenkins.views.create(view_name)
    assert view_name in jenkins.views
    assert isinstance(new_view, View) is True
    assert view_name == str(new_view)

    # Can we create a view that already exists?
    existing = jenkins.views.create(view_name)
    assert existing == new_view

    # Can we use the API convenience methods
    new_view_1 = get_view_from_url(new_view.baseurl)
    assert new_view == new_view_1

    del jenkins.views[view_name]


def test_add_job_to_view(jenkins):
    job_name = random_string()
    create_job(jenkins, job_name)

    view_name = random_string()
    assert view_name not in jenkins.views
    new_view = jenkins.views.create(view_name)
    assert view_name in jenkins.views
    assert isinstance(new_view, View) is True

    assert job_name not in new_view
    assert new_view.add_job(job_name) is True
    assert job_name in new_view
    assert isinstance(new_view[job_name], Job) is True

    assert len(new_view) == 1
    for j_name, j in new_view.iteritems():
        assert j_name == job_name
        assert isinstance(j, Job) is True

    for j in new_view.values():
        assert isinstance(j, Job) is True

    jobs = new_view.items()
    assert isinstance(jobs, list) is True
    assert isinstance(jobs[0], tuple) is True

    assert new_view.add_job(job_name) is False
    assert new_view.add_job("unknown") is False

    del jenkins.views[view_name]


def test_create_and_delete_views(jenkins):
    view1_name = random_string()
    new_view = jenkins.views.create(view1_name)
    assert isinstance(new_view, View) is True
    assert view1_name in jenkins.views
    del jenkins.views[view1_name]
    assert view1_name not in jenkins.views


def test_create_and_delete_views_by_url(jenkins):
    view1_name = random_string()
    new_view = jenkins.views.create(view1_name)
    assert isinstance(new_view, View) is True
    assert view1_name in jenkins.views

    view_url = new_view.baseurl
    view_by_url = jenkins.get_view_by_url(view_url)
    assert isinstance(view_by_url, View) is True
    jenkins.delete_view_by_url(view_url)

    assert view1_name not in jenkins.views


def test_delete_view_which_does_not_exist(jenkins):
    view1_name = random_string()
    assert view1_name not in jenkins.views
    del jenkins.views[view1_name]


def test_update_view_config(jenkins):
    view_name = random_string()
    new_view = jenkins.views.create(view_name)
    assert isinstance(new_view, View) is True
    assert view_name in jenkins.views

    config = jenkins.views[view_name].get_config().strip()
    new_view_config = VIEW_WITH_FILTER_AND_REGEX % view_name
    assert config != new_view_config

    jenkins.views[view_name].update_config(new_view_config)
    config = jenkins.views[view_name].get_config().strip()
    assert config == new_view_config


def test_make_nested_views(jenkins):
    job = create_job(jenkins)
    top_view_name = random_string()
    sub1_view_name = random_string()
    sub2_view_name = random_string()

    assert top_view_name not in jenkins.views
    tv = jenkins.views.create(top_view_name, Views.NESTED_VIEW)
    assert top_view_name in jenkins.views
    assert isinstance(tv, View) is True

    # Empty sub view
    sv1 = tv.views.create(sub1_view_name)
    assert sub1_view_name in tv.views
    assert isinstance(sv1, View) is True

    # Sub view with job in it
    tv.views[sub2_view_name] = job.name
    assert sub2_view_name in tv.views
    sv2 = tv.views[sub2_view_name]
    assert isinstance(sv2, View) is True
    assert job.name in sv2

    # Can we use the API convenience methods
    new_view = get_view_from_url(sv2.baseurl)
    assert new_view == sv2


def test_add_to_view_after_copy(jenkins):
    # This test is for issue #291
    job = create_job(jenkins)
    new_job_name = random_string()
    view_name = random_string()
    new_view = jenkins.views.create(view_name)
    new_view = jenkins.views[view_name]
    new_job = jenkins.copy_job(job.name, new_job_name)
    assert new_view.add_job(new_job.name) is True
    assert new_job.name in new_view


def test_get_job_config(jenkins):
    # This test is for issue #301
    job = create_job(jenkins)
    view_name = random_string()
    new_view = jenkins.views.create(view_name)

    assert new_view.add_job(job.name) is True

    assert "<?xml" in jenkins.get_job(job.name).get_config()
    for _, job in jenkins.views[view_name].items():
        assert "<?xml" in job.get_config()


def test_remove_job_from_view(jenkins):
    job_name = random_string()
    create_job(jenkins, job_name)

    view_name = random_string()
    assert view_name not in jenkins.views
    new_view = jenkins.views.create(view_name)
    assert view_name in jenkins.views
    assert isinstance(new_view, View)

    assert job_name not in new_view
    assert new_view.add_job(job_name)
    assert job_name in new_view
    assert isinstance(new_view[job_name], Job) is True

    assert new_view.remove_job(job_name)
    assert job_name not in new_view
    assert new_view.remove_job(job_name) is False

    del jenkins.views[view_name]
