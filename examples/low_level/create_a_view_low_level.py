"""
A low level example:
This is how JenkinsAPI creates views
"""

from __future__ import print_function
import json
import requests

url = "http://localhost:8080/createView"

str_view_name = "blahblah123"
params = {}  # {'name': str_view_name}
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {
    "name": str_view_name,
    "mode": "hudson.model.ListView",
    "Submit": "OK",
    "json": json.dumps(
        {"name": str_view_name, "mode": "hudson.model.ListView"}
    ),
}
# Try 1
result = requests.post(url, params=params, data=data, headers=headers)
print(result.text.encode("UTF-8"))
