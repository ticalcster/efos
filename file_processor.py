import logging
import logging.config

import efos
from efos.processor import Processor
from efos.webserver import WebServer

options = efos.get_options()

# Start the file processor
processor = Processor(options=options)
observer = processor.run()

# Start the weserver
httpd = WebServer(port=options.port)
httpd.start()

# Stopping
observer.stop()
observer.join()
