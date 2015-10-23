import unittest
import os
import StringIO
import shutil
import logging

import cherrypy


logging.disable(logging.CRITICAL)

WATCH_FOLDER = os.path.join(os.path.dirname(__file__), 'scans')  #: Tests watch directory
ARCHIVE_FOLDER = os.path.join(WATCH_FOLDER, 'archive')  #: Tests archive folder
OUTPUT_FOLDER = os.path.join(WATCH_FOLDER, 'output')  #: Tests output folder


def delete_file(filename):
    """Wrapper around :func:os.remove"""
    if os.path.exists(filename):
        os.remove(filename)


def copy_file(src, dst):
    """Wrapper around :func:shutil.copy"""
    shutil.copy(src, dst)


class Options:
    """Options is a dummy class to replace the ConfigArgParser options for testing."""

    def __init__(self, **kwargs):
        """
        Takes any number of kwargs and adds them as properties of the class.

        :param kwargs:
        :return:
        """
        self.watch = WATCH_FOLDER
        self.archive = ARCHIVE_FOLDER
        self.output = OUTPUT_FOLDER
        self.delete = False
        self.log_level = 11
        self.file_format = "%(eid)s.pdf"
        self.handlers = ['efos.handler.FileHandler']
        # FileHanlder
        self.disable_output = False
        # HttpHandler
        self.form_data = ['token=foobar', ]

        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class FileUploadTest(object):
    @cherrypy.expose
    def index(self):
        return """
        <html><body>
            <h2>Upload a file</h2>
            <form action="upload" method="post" enctype="multipart/form-data">
            filename: <input type="file" name="myFile" /><br />
            <input type="submit" />
            </form>
            <h2>Download a file</h2>
            <a href='download'>This one</a>
        </body></html>
        """

    @cherrypy.expose
    def upload(self, token, eid, typeid, file):
        out = """<html>
        <body>
            eid: %s<br />
            myFile length: %s<br />
            myFile filename: %s<br />
            myFile mime-type: %s
        </body>
        </html>"""

        # Although this just counts the file length, it demonstrates
        # how to read large files in chunks instead of all at once.
        # CherryPy reads the uploaded file into a temporary file;
        # myFile.file.read reads from that.
        size = 0
        while True:
            data = file.file.read(8192)
            if not data:
                break
            size += len(data)

        return out % (eid, size, file.filename, file.content_type)


cherrypy.config.update({
    'server.socket_host': '0.0.0.0',
    'server.socket_port': 9000
})

cherrypy.tree.mount(FileUploadTest(), '/', config={'/': {'tools.response_headers.on': True}})
cherrypy.engine.signals.subscribe()
