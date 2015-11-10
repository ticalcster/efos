import unittest
import os
import StringIO
import shutil

from PyPDF2 import PdfFileReader

from efos.processor import Processor
from efos.parser import Parser, File, Page, Barcode
from efos.tests import Options, delete_file, copy_file, ARCHIVE_FOLDER, OUTPUT_FOLDER, WATCH_FOLDER

__all__ = ['TestBarcodeMethods', 'TestFileMethods', 'TestPageMethods', 'TestParserMethods']


class TestBarcodeMethods(unittest.TestCase):
    def test_barcode(self):
        efos_barcode = Barcode('QRCODE', 'efos1#c#id=600144')
        self.assertTrue(efos_barcode.is_efos)
        self.assertEqual(efos_barcode.efos_sig, 'efos1#c#')
        self.assertEqual(efos_barcode.raw_data, 'id=600144')
        self.assertDictEqual(efos_barcode.data, {'id': '600144'})

        efos_barcode = Barcode('QRCODE', 'efos1#c#id=600144&date=today')
        self.assertDictEqual(efos_barcode.data, {'id': '600144', 'date': 'today'})

    def test_barcode_push_pop(self):
        efos_barcode = Barcode('QRCODE', 'efos1#c#id=600144')
        efos_barcode_child = Barcode('QRCODE', 'efos1#c#file=application')
        self.assertDictEqual(efos_barcode.data, {'id': '600144'})
        self.assertDictEqual(efos_barcode_child.data, {'file': 'application'})

        efos_barcode.push(efos_barcode_child)
        self.assertDictEqual(efos_barcode.data, {'id': '600144', 'file': 'application'})

        efos_barcode.pop()
        self.assertDictEqual(efos_barcode.data, {'id': '600144'})

    def test_barcode_c(self):
        efos_barcode = Barcode('QRCODE', 'efos1#c#id=600144')
        self.assertTrue(efos_barcode.cover_page)
        self.assertFalse(efos_barcode.merge)
        self.assertTrue(efos_barcode.new_page)
        self.assertTrue(efos_barcode.remove_page)

    def test_barcode_m(self):
        efos_barcode = Barcode('QRCODE', 'efos1#m#id=600144')
        self.assertFalse(efos_barcode.cover_page)
        self.assertTrue(efos_barcode.merge)
        self.assertFalse(efos_barcode.new_page)
        self.assertFalse(efos_barcode.remove_page)

    def test_barcode_n(self):
        efos_barcode = Barcode('QRCODE', 'efos1#n#id=600144')
        self.assertFalse(efos_barcode.cover_page)
        self.assertFalse(efos_barcode.merge)
        self.assertTrue(efos_barcode.new_page)
        self.assertFalse(efos_barcode.remove_page)

    def test_barcode_r(self):
        efos_barcode = Barcode('QRCODE', 'efos1#r#id=600144')
        self.assertFalse(efos_barcode.cover_page)
        self.assertFalse(efos_barcode.merge)
        self.assertFalse(efos_barcode.new_page)
        self.assertTrue(efos_barcode.remove_page)

    def test_barcode_cm(self):
        efos_barcode = Barcode('QRCODE', 'efos1#cm#id=600144')
        self.assertTrue(efos_barcode.cover_page)
        self.assertTrue(efos_barcode.merge)
        self.assertTrue(efos_barcode.new_page)
        self.assertTrue(efos_barcode.remove_page)

    def test_barcode_mnr(self):
        efos_barcode = Barcode('QRCODE', 'efos1#mnr#id=600144')
        self.assertFalse(efos_barcode.cover_page)
        self.assertTrue(efos_barcode.merge)
        self.assertTrue(efos_barcode.new_page)
        self.assertTrue(efos_barcode.remove_page)

    def test_barcode_none(self):
        efos_barcode = Barcode('QRCODE', 'efos1##id=600144')
        self.assertFalse(efos_barcode.cover_page)
        self.assertFalse(efos_barcode.merge)
        self.assertFalse(efos_barcode.new_page)
        self.assertFalse(efos_barcode.remove_page)


class TestPageMethods(unittest.TestCase):
    def test_efos_page(self):
        filename = os.path.join(WATCH_FOLDER, 'efos_page.pdf')
        pdf_file = PdfFileReader(filename, strict=False)
        efos_page = Page(pdf_file.getPage(0))
        self.assertTrue(efos_page.is_efos)
        self.assertEqual(efos_page.get_barcode().data.get('id'), '600000')


class TestFileMethods(unittest.TestCase):
    def setUp(self):
        self.options = Options()
        self.filename = os.path.join(WATCH_FOLDER, 'doc_multi.pdf')
        self.pdf_file = PdfFileReader(self.filename, strict=False)
        self.barcode = Barcode('QRCODE', 'efos1#c#id=600000')

        self.save_as = os.path.join(WATCH_FOLDER, 'test_save.pdf')
        delete_file(self.save_as)

    def test_file_page_count(self):
        new_file = File(self.barcode, self.options.file_format)
        new_file.add(Page(self.pdf_file.getPage(0)))
        self.assertEqual(new_file.page_count, 1)
        new_file.add(Page(self.pdf_file.getPage(1)))
        self.assertEqual(new_file.page_count, 2)

    def test_file_filename(self):
        new_file = File(self.barcode, os.path.join(OUTPUT_FOLDER, '%(id)s.pdf'))
        self.assertEqual(new_file.basename, '600000.pdf')
        self.assertEqual(new_file.get_filename(), os.path.join(OUTPUT_FOLDER, '600000.pdf'))

    def test_file_write(self):
        f = open(self.save_as, 'w+b')
        new_file = File(self.barcode, self.options.file_format)
        new_file.add(Page(self.pdf_file.getPage(0)))
        new_file.add(Page(self.pdf_file.getPage(1)))
        new_file.write(f)
        self.assertEqual(os.path.isfile(self.save_as), True)

    def test_file_write_stream(self):
        stream = StringIO.StringIO()
        new_file = File(self.barcode, self.options.file_format)
        new_file.add(Page(self.pdf_file.getPage(0)))
        new_file.add(Page(self.pdf_file.getPage(1)))
        new_file.write(stream)
        self.assertGreater(len(stream.getvalue()), 10)  # TODO: better test?


class TestParserMethods(unittest.TestCase):
    def setUp(self):
        self.options = Options()
        self.filename = os.path.join(WATCH_FOLDER, 'doc_multi.pdf')

        self.file_600000 = os.path.join(OUTPUT_FOLDER, '600000.pdf')
        self.file_600001 = os.path.join(OUTPUT_FOLDER, '600001.pdf')
        delete_file(self.file_600000)
        delete_file(self.file_600001)

    def test_parser_init(self):
        parser = Parser(filename=self.filename, options=self.options)
        self.assertEqual(parser.filename, os.path.join(WATCH_FOLDER, 'doc_multi.pdf'))
        self.assertEqual(parser.file_count, 0)

    def test_parser_filename_format(self):
        parser = Parser(filename=self.filename, options=self.options)
        self.assertEqual(parser.get_filename_format(), '%(id)s.pdf')

    def test_parser_parse(self):
        parser = Parser(filename=self.filename, options=self.options)
        parser.parse()
        self.assertEqual(parser.file_count, 2)

        parser.process()
        self.assertTrue(os.path.isfile(self.file_600000))
        self.assertTrue(os.path.isfile(self.file_600001))

    def test_parser_delete(self):
        filename = os.path.join(WATCH_FOLDER, 'doc_multi_delete.pdf')
        archive_filename = os.path.join(ARCHIVE_FOLDER, 'doc_multi_delete.pdf')
        copy_file(self.filename, filename)
        parser = Parser(filename=filename, options=Options(archive=False, delete=True,
                                                           file_format="%(id)s_delete.pdf"))

        parser.delete()
        self.assertFalse(os.path.exists(archive_filename))  # archived
        self.assertFalse(os.path.exists(filename))  # deleted
