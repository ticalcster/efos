import unittest
import os
import StringIO
import shutil

from PyPDF2 import PdfFileReader
import cherrypy
import requests

from efos.processor import Processor
from efos.parser import Parser, File, Page, Barcode
from efos.handler import HttpHandler
from efos.tests import Options, delete_file, copy_file, ARCHIVE_FOLDER, OUTPUT_FOLDER, WATCH_FOLDER, FileUploadTest


class TestFileHanlder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cherrypy.config.update({
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 9000
        })

        cherrypy.tree.mount(FileUploadTest(), '/', config={'/': {'tools.response_headers.on': True}})
        cherrypy.engine.signals.subscribe()
        cherrypy.engine.start()

    @classmethod
    def tearDownClass(cls):
        cherrypy.engine.exit()

    def setUp(self):
        self.options = Options()
        self.barcode = Barcode('QRCODE', 'efos1#c#eid=600144')

    def test_http_form_data(self):
        handler = HttpHandler(self.options)
        file = File(self.barcode, filename_format="%(eid)s.pdf")

        form_data = handler.get_form_data(file)

        self.assertDictEqual(form_data, {'token': 'foobar', 'eid': '600144'})

    def test_http_call(self):
        r = requests.get('http://localhost:9000/')
        self.assertEquals(r.status_code, 200)


class TestHttpHanlder(unittest.TestCase):
    def test_efos_page(self):
        filename = os.path.join(WATCH_FOLDER, 'efos_page.pdf')
        pdf_file = PdfFileReader(filename, strict=False)
        efos_page = Page(pdf_file.getPage(0))
        self.assertTrue(efos_page.is_efos)
        self.assertEqual(efos_page.get_barcode().data.get('eid'), '600144')
