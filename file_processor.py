__author__ = 'kclark'
import logging

from efos.processor import Processor

FORMAT = '%(message)s'
logging.basicConfig(level=1)
log = logging.getLogger(__name__)

processor = Processor(watch='test\scans')
log.warning("test")
log.debug("test")
processor.run()
