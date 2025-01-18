"""
Save this file as server.py
>>> python server.py 0.0.0.0 8001
serving on 0.0.0.0:8001

or simply

>>> python server.py
Serving on localhost:8000

You can use this to test GET and POST methods.

In order to run this example you will need the six compatibility library
install it with pip before running this script:

```
pip install six
```
"""

from six.moves import SimpleHTTPServer, socketserver
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
