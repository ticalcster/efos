__author__ = 'kclark'
import logging
import os

import configargparse

from efos.processor import Processor
from efos.webserver import WebServer

# Config / Arg stuffs
cap = configargparse.ArgParser(default_config_files=['efos.conf',])
cap.add('-a', '--archive', default="archive", help='directory to archive files')
cap.add('-c', '--config', is_config_file=True, help='path to config file')
cap.add('-d', '--delete', action="store_true", help='delete files after processing')
cap.add('-l', '--log-level', default=11, type=int, help='logging level [1-50+]')
cap.add('-w', '--watch', required=True, help='directory to watch for files')

options = cap.parse_args()

FORMAT = '%(message)s'
logging.basicConfig(level=options.log_level)
log = logging.getLogger(__name__)

logging.debug(options)


archive_path = ""
if options.archive:
    if os.path.isabs(options.archive):
        archive_path = options.archive
    else:
        archive_path = os.path.join(options.watch, options.archive)

processor = Processor(watch=options.watch, archive=archive_path, delete=options.delete)
processor.run()


httpd = WebServer()
httpd.serve_forever()
