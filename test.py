import unittest
import os
import logging

from efos.tests.test_parser import *

if __name__ == '__main__':
    # set up logging
    logging.disable(logging.CRITICAL)

    filelist = [os.remove(os.path.join('tests', 'archive', f)) for f in os.listdir(os.path.join('tests', 'archive')) if
                f.endswith(".pdf")]
    unittest.main()
