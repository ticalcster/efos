import unittest
import os
import StringIO
import shutil

from PyPDF2 import PdfFileReader

from efos.processor import Processor
from efos.parser import Parser, File, Page, Barcode
from efos.tests import Options, delete_file, copy_file

__all__ = ['TestBarcodeMethods', 'TestFileMethods', 'TestPageMethods', 'TestParserMethods']


class TestBarcodeMethods(unittest.TestCase):
    def test_barcode(self):
        efos_barcode = Barcode('QRCODE', 'efos1#{"eid": 600144}')
        self.assertTrue(efos_barcode.is_efos)
        self.assertEqual(efos_barcode.efos_sig, 'efos1#')
        self.assertEqual(efos_barcode.raw_data, '{"eid": 600144}')
        self.assertDictEqual(efos_barcode.data, {'eid': 600144})


class TestPageMethods(unittest.TestCase):
    def test_efos_page(self):
        filename = os.path.join('tests', 'efos_page.pdf')
        pdf_file = PdfFileReader(filename)
        efos_page = Page(pdf_file.getPage(0))
        self.assertTrue(efos_page.is_efos)
        self.assertEqual(efos_page.get_barcode().data.get('eid'), 600144)


class TestFileMethods(unittest.TestCase):
    def setUp(self):
        self.options = Options()
        self.filename = os.path.join('tests', 'doc_multi.pdf')
        self.pdf_file = PdfFileReader(self.filename)
        self.barcode = Barcode('QRCODE', 'efos1#{"eid": 600144}')

        self.save_as = os.path.join('tests', 'test_save.pdf')
        delete_file(self.save_as)

    def test_file_page_count(self):
        new_file = File(self.barcode, self.options.file_format)
        new_file.add(Page(self.pdf_file.getPage(0)))
        self.assertEqual(new_file.page_count, 1)
        new_file.add(Page(self.pdf_file.getPage(1)))
        self.assertEqual(new_file.page_count, 2)

    def test_file_filename(self):
        new_file = File(self.barcode, os.path.join('tests', 'output', '%(eid)s.pdf'))
        self.assertEqual(new_file.basename, '600144.pdf')
        self.assertEqual(new_file.get_filename(), os.path.join('tests', 'output', '600144.pdf'))

    def test_file_save(self):
        new_file = File(self.barcode, self.options.file_format)
        new_file.add(Page(self.pdf_file.getPage(0)))
        new_file.add(Page(self.pdf_file.getPage(1)))
        new_file.save(self.save_as)
        self.assertEqual(os.path.isfile(self.save_as), True)

    def test_file_write(self):
        stream = StringIO.StringIO()
        new_file = File(self.barcode, self.options.file_format)
        new_file.add(Page(self.pdf_file.getPage(0)))
        new_file.add(Page(self.pdf_file.getPage(1)))
        new_file.write(stream)
        self.assertGreater(len(stream.getvalue()), 10)  # TODO: better test?


class TestParserMethods(unittest.TestCase):
    def setUp(self):
        self.options = Options()
        self.filename = os.path.join('tests', 'doc_multi.pdf')

        self.file_600144 = os.path.join('tests', 'output', '600144.pdf')
        self.file_600155 = os.path.join('tests', 'output', '600155.pdf')
        delete_file(self.file_600144)
        delete_file(self.file_600155)

    def test_parser_init(self):
        parser = Parser(filename=self.filename, options=self.options)
        self.assertEqual(parser.filename, os.path.join('tests', 'doc_multi.pdf'))
        self.assertEqual(parser.file_count, 0)

    def test_parser_filename_formate(self):
        parser = Parser(filename=self.filename, options=self.options)
        self.assertEqual(parser.get_filename_format(), os.path.join('tests', 'output', '%(eid)s.pdf'))

    def test_parser_parse(self):
        parser = Parser(filename=self.filename, options=self.options)
        parser.parse()
        self.assertEqual(parser.file_count, 2)

        parser.process()
        self.assertTrue(os.path.isfile(self.file_600144))
        self.assertTrue(os.path.isfile(self.file_600155))

    def test_parser_archive(self):
        filename = os.path.join('tests', 'doc_multi_archive.pdf')
        archive_filename = os.path.join('tests', 'archive', 'doc_multi_archive.pdf')
        copy_file(self.filename, filename)
        parser = Parser(filename=filename, options=Options(archive=os.path.join('tests', 'archive'), delete=False,
                                                           file_format="%(eid)s_archive.pdf"))
        parser.archive_delete()
        self.assertTrue(os.path.exists(archive_filename))  # archived
        self.assertTrue(os.path.exists(filename))  # deleted

    def test_parser_delete(self):
        filename = os.path.join('tests', 'doc_multi_delete.pdf')
        archive_filename = os.path.join('tests', 'archive', 'doc_multi_delete.pdf')
        copy_file(self.filename, filename)
        parser = Parser(filename=filename, options=Options(archive="", delete=True,
                                                           file_format="%(eid)s_delete.pdf"))
        parser.archive_delete()
        self.assertFalse(os.path.exists(archive_filename))  # archived
        self.assertFalse(os.path.exists(filename))  # deleted

    def test_parser_archive_delete(self):
        filename = os.path.join('tests', 'doc_multi_archive_delete.pdf')
        archive_filename = os.path.join('tests', 'archive', 'doc_multi_archive_delete.pdf')
        copy_file(self.filename, filename)
        parser = Parser(filename=filename, options=Options(archive=os.path.join('tests', 'archive'), delete=True,
                                                           file_format="%(eid)s_archive_delete.pdf"))
        parser.archive_delete()
        self.assertTrue(os.path.exists(archive_filename))  # archived
        self.assertFalse(os.path.exists(filename))  # deleted
