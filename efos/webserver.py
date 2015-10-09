import threading
import time
import random
import os

import cherrypy

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage

cur_dir = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
index_path = os.path.join(cur_dir,'html', 'index.html')
index_page = file(index_path, 'r').read()


class ChatWebSocketHandler(WebSocket):
    def received_message(self, m):
        cherrypy.engine.publish('websocket-broadcast', m)

    def closed(self, code, reason="A client left the room without a proper explanation."):
        cherrypy.engine.publish('websocket-broadcast', TextMessage(reason))


class ChatWebApp(object):
    # def __init__(self):
    #     super(ChatWebApp, self).__init__()

    @cherrypy.expose
    def index(self):
        return index_page % {'username': "User%d" % random.randint(50, 1000),
                             'ws_addr': 'ws://localhost:8081/ws'}

    @cherrypy.expose
    def ws(self):
        cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))


class WebServer:
    def __init__(self, host='0.0.0.0', port=8081, index='index.html'):
        self.port = port
        self.host = host

    def start(self):
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
