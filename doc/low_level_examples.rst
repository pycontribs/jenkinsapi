Low level examples of module code
=================================

Below examples detail out how the api does things internally

Copy an existing job - jenkins.copy_job()
-----------------------------------------

.. code-block:: python

   import requests
   from pkg_resources import resource_string
   from jenkinsapi.jenkins import Jenkins
   from jenkinsapi_tests.test_utils.random_strings import random_string

   J = Jenkins("http://localhost:8080")
   jobName = random_string()
   jobName2 = "%s_2" % jobName

   url = "http://localhost:8080/createItem?from=%s&name=%s&mode=copy" % (
       jobName,
       jobName2,
   )

   xml = resource_string("examples", "addjob.xml")
   j = J.create_job(jobname=jobName, xml=xml)


   h = {"Content-Type": "application/x-www-form-urlencoded"}
   response = requests.post(url, data="dysjsjsjs", headers=h)
   print(response.text.encode("UTF-8"))

Create a view - jenkins.views.create()
--------------------------------------

.. code-block:: python

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

Run a parameterized build - jenkins.build_job()
-----------------------------------------------

.. code-block:: python

   import json
   import requests

   toJson = {"parameter": [{"name": "B", "value": "xyz"}]}
   url = "http://localhost:8080/job/ddd/build"
   # url = 'http://localhost:8000'
   headers = {"Content-Type": "application/x-www-form-urlencoded"}
   form = {"json": json.dumps(toJson)}
   response = requests.post(url, data=form, headers=headers)
   print(response.text.encode("UTF-8"))

How JenkinsAPI logs in with authentication
------------------------------------------

.. code-block:: python

    from jenkinsapi import jenkins

    J = jenkins.Jenkins("http://localhost:8080", username="sal", password="foobar")
    J.poll()
    print(J.items())

How JenkinsAPI watches post requests
------------------------------------

.. code-block:: python

    import http.server as SimpleHTTPServer
    import socketserver
    import logging
    import cgi

    PORT = 8081  # <-- change this to be the actual port you want to run on
    INTERFACE = "localhost"


    class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def do_GET(self):
            logging.warning("======= GET STARTED =======")
            logging.warning(self.headers)
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

        def do_POST(self):
            logging.warning("======= POST STARTED =======")
            logging.warning(self.headers)
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers["Content-Type"],
                },
            )
            logging.warning("======= POST VALUES =======")
            for item in form.list:
                logging.warning(item)
            logging.warning("\n")
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


    Handler = ServerHandler

    httpd = socketserver.TCPServer(("", PORT), Handler)

    print(
        "Serving at: http://%(interface)s:%(port)s"
        % dict(interface=INTERFACE or "localhost", port=PORT)
    )
    httpd.serve_forever()
