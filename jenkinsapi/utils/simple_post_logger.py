#!/usr/bin/env python
from __future__ import print_function

try:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
except ImportError:
    from http.server import SimpleHTTPRequestHandler

try:
    import SocketServer as socketserver
except ImportError:
    import socketserver

import logging
import cgi

PORT = 8080


class ServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        logging.error(self.headers)
        super().do_GET()

    def do_POST(self):
        logging.error(self.headers)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers["Content-Type"],
            },
        )
        for item in form.list:
            logging.error(item)
        super().do_GET()


if __name__ == "__main__":
    Handler = ServerHandler

    httpd = socketserver.TCPServer(("", PORT), Handler)

    print("serving at port", PORT)
    httpd.serve_forever()
