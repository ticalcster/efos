import unittest
import os
import logging
import cherrypy

from efos.tests import ARCHIVE_FOLDER, OUTPUT_FOLDER, WATCH_FOLDER, FileUploadTest

from efos.tests.test_parser import *
from efos.tests.test_handler import *

if __name__ == '__main__':
    # set up logging


    try:
        filelist = [os.remove(os.path.join(ARCHIVE_FOLDER, f)) for f in os.listdir(ARCHIVE_FOLDER) if
                    f.endswith(".pdf")]
    except:
        pass  # if can't delete they probably not there to begin with.


    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 9000
    })

    # cherrypy.tree.mount(FileUploadTest(), '/', config={})
    # cherrypy.engine.signals.subscribe()
    # cherrypy.engine.start()

    print('-----', 'starting tests')
    #logging.disable(logging.CRITICAL)
    unittest.main()
    #logging.disable(logging.DEBUG)

    print('-----', "tests done")
    # cherrypy.engine.exit()
    print('-----', "test file exit")
    #cherrypy.engine.block()
