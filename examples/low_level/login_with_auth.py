"""
A lower level example of how we login with authentication
"""

from jenkinsapi import jenkins


J = jenkins.Jenkins("http://localhost:8080", username="sal", password="foobar")
J.poll()

print(J.items())
