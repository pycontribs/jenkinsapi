# '''
# System tests for `jenkinsapi.jenkins` module.
# '''
# import unittest
# from jenkinsapi_tests.systests.base import BaseSystemTest
# from jenkinsapi_tests.test_utils.random_strings import random_string
# from jenkinsapi_tests.systests.job_configs import SCM_GIT_JOB

# # Maybe have a base class for all SCM test activites?
# class TestSCMGit(BaseSystemTest):
#     # Maybe it makes sense to move plugin dependencies outside the code.
#     # Have a config to dependencies mapping from the launcher can use
#     # to install plugins.
#     def test_get_revision(self):
#         job_name = 'git_%s' % random_string()
#         job = self.jenkins.create_job(job_name, SCM_GIT_JOB)
#         ii = job.invoke()
#         ii.block(until='completed')
#         self.assertFalse(ii.is_running())
#         b = ii.get_build()
#         try:
#             self.assertIsInstance(b.get_revision(), basestring)
#         except NameError:
#             # Python3
#             self.assertIsInstance(b.get_revision(), str)

# if __name__ == '__main__':
#     unittest.main()
