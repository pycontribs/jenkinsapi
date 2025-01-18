"""
Get information about currently installed plugins
"""

from __future__ import print_function
from jenkinsapi.jenkins import Jenkins


plugin_name = "subversion"
jenkins = Jenkins("http://localhost:8080")
plugin = jenkins.get_plugins()[plugin_name]

print(repr(plugin))
