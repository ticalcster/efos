import unittest
import os
import logging

from efos.tests import ARCHIVE_FOLDER, OUTPUT_FOLDER, WATCH_FOLDER
from efos.tests.test_parser import *

if __name__ == '__main__':
    # set up logging
    logging.disable(logging.CRITICAL)

    try:
        filelist = [os.remove(os.path.join(ARCHIVE_FOLDER, f)) for f in os.listdir(ARCHIVE_FOLDER) if f.endswith(".pdf")]
    except:
        pass  # if can't delete they probably not there to begin with.
    unittest.main()
