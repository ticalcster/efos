import unittest
import os
import StringIO
import shutil


WATCH_FOLDER = os.path.join(os.path.dirname(__file__), 'scans')
ARCHIVE_FOLDER = os.path.join(WATCH_FOLDER, 'archive')
OUTPUT_FOLDER = os.path.join(WATCH_FOLDER, 'output')


def delete_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


def copy_file(src, dst):
    shutil.copy(src, dst)


class Options:
    def __init__(self, **kwargs):
        self.watch = WATCH_FOLDER
        self.archive = ARCHIVE_FOLDER
        self.output = OUTPUT_FOLDER
        self.delete = False
        self.log_level = 11
        self.file_format = "%(eid)s.pdf"
        self.handlers = ['efos.handler.FileHandler']

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
