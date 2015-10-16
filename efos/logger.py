import sys
from logging import Handler, INFO, DEBUG, WARN, WARNING, ERROR, CRITICAL
import json

import cherrypy
from ws4py.messaging import TextMessage


class WSHandler(Handler):
    """
    Log handler used to send notifications to HipChat
    """

    # def __init__(self, token, room,
    #             sender='Django', notify=False, color='yellow', colors={}):
    #     """
    #     :param token: the auth token for access to the API - see hipchat.com
    #     :param room: the numerical id of the room to send the message to
    #     :param sender (optional): the 'from' property of the message - appears in the HipChat window
    #     :param notify (optional): if True, HipChat pings / bleeps / flashes when message is received
    #     :param color (optional): sets the background color of the message in the HipChat window
    #     :param colors (optional): a dict of level:color pairs (e.g. {'DEBUG:'red'} used to
    #                                 override the default color)
    #     """
    #     Handler.__init__(self)
    #     self.token = token
    #     self.room = room
    #     self.sender = sender
    #     self.notify = notify
    #     self.color = color
    #     self.colors = colors

    bootstrap_levels = {'CRITICAL': 'danger',
                        'ERROR': 'danger',
                        'WARNING': 'warning',
                        'INFO': 'primary',
                        'DEBUG': 'muted'}

    def emit(self, record):
        self.format(record)
        try:
            msg = {
                'created': record.asctime,
                'name': record.name,
                'level': self.bootstrap_levels[record.levelname],
                'message': record.getMessage(),
                'funcName': record.funcName,
                'module': record.module,
                'pathname': record.pathname,
                'filename': record.filename
            }
            cherrypy.engine.publish('websocket-broadcast', json.dumps(msg))
        except:
            print sys.exc_info()[1]
            self.handleError(record)


