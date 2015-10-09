# -*- coding: utf-8 -*-
__doc__ = """
A simple chat example using a CherryPy webserver.
$ pip install cherrypy
Then run it as follow:
$ python app.py
You will want to edit this file to change the
ws_addr variable used by the websocket object to connect
to your endpoint. Probably using the actual IP
address of your machine.
"""
import threading
from time import sleep
import random
import os

import cherrypy

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage

cur_dir = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
index_path = os.path.join(cur_dir, 'index.html')
index_page = file(index_path, 'r').read()

class ChatWebSocketHandler(WebSocket):
    def received_message(self, m):
        cherrypy.engine.publish('websocket-broadcast', m)

    def closed(self, code, reason="A client left the room without a proper explanation."):
        cherrypy.engine.publish('websocket-broadcast', TextMessage(reason))

class ChatWebApp(object):
    @cherrypy.expose
    def index(self):
        return index_page % {'username': "User%d" % random.randint(50, 1000),
                             'ws_addr': 'ws://localhost:9000/ws'}

    @cherrypy.expose
    def ws(self):
        cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))


def send_message():
    while True:
        sleep(5)
        cherrypy.engine.publish('websocket-broadcast', TextMessage("It's Time"))

if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8081
    })
    
    WebSocketPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool()



    t = threading.Thread(target=send_message)
    t.setDaemon(True)
    t.start()


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
