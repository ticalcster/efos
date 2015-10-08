import SimpleHTTPServer
import SocketServer
import logging

log = logging.getLogger(__name__)

class WebServer():
    def __init__(self):
        self.port = 8081
        self.handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        self.httpd = SocketServer.TCPServer(("", self.port), self.handler)

        log.info("serving at port: %s" % self.port)

    def serve_forever(self):
        self.httpd.serve_forever()
