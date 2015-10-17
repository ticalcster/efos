import threading
import time
import random
import os
import StringIO

import pyqrcode

import cherrypy
from cherrypy.lib import file_generator

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage

from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader('efos', 'html'))


class ChatWebSocketHandler(WebSocket):
    def received_message(self, m):
        """ """
        cherrypy.engine.publish('websocket-broadcast', m)

    def closed(self, code, reason="A client left the room without a proper explanation."):
        """ """
        cherrypy.engine.publish('websocket-broadcast', TextMessage(reason))


class ChatWebApp(object):
    # def __init__(self, host, port):
    #     super(ChatWebApp, self).__init__()
    #     self.ws_addr = "ws://%s:%s/ws" % (host, port)

    @cherrypy.expose
    def index(self):
        """ """
        ws_addr = "ws://%s/ws" % cherrypy.request.headers['host']
        template = env.get_template('index.html')
        return template.render(ws_addr=ws_addr)

    @cherrypy.expose
    def generate(self):
        """ """
        template = env.get_template('generate.html')
        return template.render()

    @cherrypy.expose
    def logs(self):
        """ """
        ws_addr = "ws://%s/ws" % cherrypy.request.headers['host']
        template = env.get_template('logs.html')
        return template.render(ws_addr=ws_addr)

    @cherrypy.expose
    def barcode(self, data, scale=4):
        """ """
        cherrypy.response.headers['Content-Type'] = "image/png"
        buffer = StringIO.StringIO()
        code = pyqrcode.create(data)
        code.png(buffer, scale=scale)
        buffer.seek(0)
        return file_generator(buffer)

    @cherrypy.expose
    def ws(self):
        """ """
        cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))


class WebServer:
    def __init__(self, host='0.0.0.0', port=8081):
        """ """
        self.port = port
        self.host = host

    def start(self):
        """ """
        cherrypy.config.update({
            'server.socket_host': self.host,
            'server.socket_port': self.port
        })

        WebSocketPlugin(cherrypy.engine).subscribe()
        cherrypy.tools.websocket = WebSocketTool()

        cherrypy.quickstart(ChatWebApp(), '',
                            config={
                                '/': {
                                    'tools.response_headers.on': True,
                                    'tools.response_headers.headers': [
                                        ('X-Frame-options', 'deny'),
                                        ('X-XSS-Protection', '1; mode=block'),
                                        ('X-Content-Type-Options', 'nosniff')
                                    ]
                                },
                                '/ws': {
                                    'tools.websocket.on': True,
                                    'tools.websocket.handler_cls': ChatWebSocketHandler
                                },
                            })
