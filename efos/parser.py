import logging
import os
import StringIO
import json
import re
import shutil

from wand.image import Image as WandImage
from PIL import Image as PILImage
from PyPDF2 import PdfFileReader, PdfFileWriter
import zbar

from efos import log, get_handlers

EFOSSIG = '^efos\d#'


class Barcode():
    def __init__(self, encoding, data):
        self._efos_sig = None
        self.type = encoding  # QRCODE
        self.raw = data
        self.raw_data = data
        self.data = data

        if self.is_efos:
            try:
                self.data = json.loads(self.raw_data)
            except:
                log.error("Could not parse json from QR Code.")

    @property
    def efos_sig(self):
        if self.is_efos:
            return self._efos_sig
        return None

    @property
    def is_efos(self):
        if self._efos_sig:
            return True
        try:
            self._efos_sig = re.match(EFOSSIG, self.raw_data).group()
            self.raw_data = self.raw_data.replace(self._efos_sig, "")
            log.debug('efos sig found: %s' % self.raw_data)
            return True
        except:
            pass
        log.debug('regex not found: %s' % self.raw_data)
        return False


class Page():
    def __init__(self, page=None):
        self._barcodes = None
        self._efos_barcode = None
        self.page = page


        # save single page to stream
        page_stream = StringIO.StringIO()
        pdf_file_writer = PdfFileWriter()
        pdf_file_writer.addPage(self.page)
        pdf_file_writer.write(page_stream)


        # Convert pdf file to image
        image_stream = StringIO.StringIO()
        pdf_image = WandImage(blob=page_stream.getvalue())
        png_image = pdf_image.convert('png')
        # self.image.type = 'grayscale'
        png_image.save(file=image_stream)

        # Convert Image to B/W
        self.pil_image = PILImage.open(image_stream)
        self.get_barcodes()

    def get_barcodes(self):
        img = self.pil_image.convert('L')

        width, height = img.size
        raw = img.tostring()

        # create a reader
        scanner = zbar.ImageScanner()

        # configure the reader
        scanner.parse_config('enable')

        # wrap image data
        image = zbar.Image(width, height, 'Y800', raw)

        # scan the image for barcodes
        scanner.scan(image)
        # extract results
        self._barcodes = []
        for symbol in image:
            # do something useful with results
            self._barcodes.append(Barcode(symbol.type, symbol.data))
        # print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data

        # clean up
        del (image)
        return self._barcodes

    @property
    def is_efos(self):
        """Returns true if there is an efos barcode"""
        for barcode in self.get_barcodes():
            if barcode.is_efos:
                self._efos_barcode = barcode
                return True
        return False

    def get_barcode(self):
        """Gets the efos barcode or returns None."""
        if self.is_efos:
            return self._efos_barcode
        return None

    def get_ascii(self, ):
        # resize to: the max of the img is maxLen
        img = self.pil_image.copy()

        maxLen = 60.0  # default maxlen: 100px  # TODO: setting
        width, height = img.size

        rate = maxLen / max(width, height)

        ascii_ratio = (7.0 / 9.0)  # TODO: setting

        width = int(rate * width)  # cast to int
        height = int((rate * height) * ascii_ratio)

        img = img.resize((width, height))

        # img = img.convert('L')

        # get pixels
        pixel = img.load()

        # grayscale
        color = "MNHQ$OC?7>!:-;. "  # length 16

        ascii = StringIO.StringIO()

        for w in xrange(width + 2):
            ascii.write('-')
        ascii.write('\n')

        for h in xrange(height):  # first go through the height,  otherwise will roate
            ascii.write('|')
            for w in xrange(width):
                rgb = pixel[w, h]
                # string += "%s," % rgb
                ascii.write(color[int(rgb / 256.0 * 16)])
            ascii.write('|')
            ascii.write('\n')

        for w in xrange(width + 2):
            ascii.write('-')
        ascii.write('\n')

        return ascii.getvalue()


class File():
    def __init__(self, barcode, filename_format=None):
        self._filename_format = filename_format
        self.barcode = barcode
        self.pages = []
        self._filename = None
        self.valid_filename = False

    @property
    def page_count(self):
        return len(self.pages)

    @property
    def basename(self):
        return os.path.basename(self.get_filename())

    def get_filename(self):
        if self._filename:
            return self._filename

        self._filename = self.barcode.raw
        try:
            self._filename = self._filename_format % self.barcode.data
        except KeyError as ex:
            log.warning("Barcode does not contain %s which is required by file-format" % ex)
        except Exception as ex:
            log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.message, 'args': ex.args})
        return self._filename

    def add(self, page):
        self.pages.append(page)

    def write(self, output):
        pdf_file_writer = PdfFileWriter()
        for page in self.pages:
            pdf_file_writer.addPage(page.page)
        pdf_file_writer.write(output)


class Parser():
    def __init__(self, filename=None, options=None):
        if not options:
            log.critical('No options passed to Parser')
            raise ValueError('No Options')
        self.options = options
        self.filename = filename
        self.files = []
        self.handlers = get_handlers(self.options)

        try:
            if not os.path.exists(self.filename):
                print "File path is invalid."
            elif not os.path.isfile(self.filename):
                print "File does not exist."
            elif not os.access(self.filename, os.R_OK):
                print "File cannot be read."
            else:
                self.pdf_file = PdfFileReader(self.filename)
        except IOError as ex:
            print "I/O error({0}): {1}".format(ex.errno, ex.strerror)

    @property
    def file_count(self):
        return len(self.files)

    def parse(self):
        new_file = None
        for pdf_page in self.pdf_file.pages:
            page = Page(page=pdf_page)

            if page.is_efos:
                new_file = self.new_file(page.get_barcode())
                log.info("Creating page %s" % new_file.get_filename())
            elif file:
                new_file.add(page)
                log.debug("Adding page to %s" % new_file.get_filename())

    def process(self):
        for file in self.files:
            for handler in self.handlers:
                handler.process(file)

        self.archive_delete()

    def archive_delete(self):
        # After Parsing, Archive and Delete
        if self.options.archive:
            archive_filename = os.path.join(self.options.archive, self.filename.replace(self.options.watch, "")[1:])
            if self.options.delete:
                log.info("Moving file %s to %s" % (self.filename, archive_filename))
                os.rename(self.filename, archive_filename)
            else:
                log.info("Archiving file %s to %s" % (self.filename, archive_filename))
                shutil.copy(self.filename, archive_filename)
        elif self.options.delete:
            if os.path.exists(self.filename):
                os.remove(self.filename)
                log.info("Removing file %s" % (self.filename,))

    def new_file(self, barcode):
        file = File(barcode, filename_format=self.get_filename_format())
        self.files.append(file)
        return file

    def get_filename_format(self):
        return os.path.normpath(os.path.join(self.options.output, self.options.file_format))
