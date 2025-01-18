"""
How to delete slaves/nodes
"""

from __future__ import print_function
import logging
from jenkinsapi.jenkins import Jenkins

logging.basicConfig()


j = Jenkins("http://localhost:8080")

for node_id, _ in j.get_nodes().iteritems():
    if node_id != "master":
        print(node_id)
        j.delete_node(node_id)

# Alternative way - this method will not delete 'master'
for node in j.nodes.keys():
    del j.nodes[node]
