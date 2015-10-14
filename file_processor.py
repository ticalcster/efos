__author__ = 'kclark'
import logging
import logging.config
import os
import threading
import time

import configargparse
import cherrypy
from ws4py.messaging import TextMessage

from efos import LOGGING_CONFIG
from efos.processor import Processor
from efos.webserver import WebServer
# from efos.processor import websocket_timer


# Config / Arg stuffs
cap = configargparse.ArgParser(default_config_files=['efos.conf', ])
cap.add('-a', '--archive', default="archive", help='directory to archive files')
cap.add('-c', '--config', is_config_file=True, help='path to config file')
cap.add('-d', '--delete', action="store_true", help='delete files after processing')
cap.add('-f', '--file-format', default="%(filename)s", help='filename format from kwargs in QRCode')
cap.add('-l', '--log-level', default=11, type=int, help='logging level [1-50+]')
cap.add('-o', '--output', default="output", help='directory to output files')
cap.add('-p', '--port', default=8081, type=int, help='web server port')
cap.add('-w', '--watch', required=True, help='directory to watch for files')

options = cap.parse_args()

FORMAT = '%(message)s'
#logging.basicConfig(level=options.log_level)
log = logging.getLogger()


if options.archive:
    if not os.path.isabs(options.archive):
        options.archive = os.path.join(options.watch, options.archive)

if options.output:
    if not os.path.isabs(options.output):
        options.output = os.path.join(options.watch, options.output)

processor = Processor(options=options)
observer = processor.run()


def websocket_timer(e, t):
    while not e.isSet():
        e.wait(t)
        cherrypy.engine.publish('websocket-broadcast', TextMessage('Times up!'))
        time.sleep(1)
    log.info("stopping the Processor")


# e = threading.Event()
# t = threading.Thread(target=websocket_timer, args=(e, 1))
# t.setDaemon(True)
# t.start()

httpd = WebServer(port=options.port)
httpd.start()

# e.set()
# t.join()
observer.stop()
observer.join()
