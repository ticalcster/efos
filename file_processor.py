__author__ = 'kclark'
import logging

from efos.processor import Processor
from efos.webserver import WebServer

FORMAT = '%(message)s'
logging.basicConfig(level=11)
log = logging.getLogger(__name__)


processor = Processor(watch='/home/vagrant/scans')
log.warning("test")
log.debug("test")
processor.run()


httpd = WebServer()
httpd.serve_forever()