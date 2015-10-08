import unittest
import os

from PyPDF2 import PdfFileReader

from efos.processor import Parser, Page, Barcode


class TestStringMethods(unittest.TestCase):

    def test_barcode(self):
        efos_barcode = Barcode('QRCODE', 'efos1#{"eid": 600155}')
        self.assertTrue(efos_barcode.is_efos)
        self.assertEqual(efos_barcode.efos_sig, 'efos1#')
        self.assertEqual(efos_barcode.raw_data, '{"eid": 600155}')
        self.assertDictEqual(efos_barcode.data, {'eid': 600155})

    def test_page(self):
        filename = os.path.join('tests', 'efos_page.pdf')
        pdf_file = PdfFileReader(filename)
        efos_page = Page(pdf_file.getPage(0))
        self.assertTrue(efos_page.is_efos)
        self.assertEqual(efos_page.get_barcode().data.get('eid'), 600144)

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()
