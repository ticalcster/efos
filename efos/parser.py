import logging
import os
import StringIO
import json
import re
import shutil
import urlparse

from wand.image import Image as WandImage
from PIL import Image as PILImage
from PyPDF2 import PdfFileReader, PdfFileWriter
import zbar

from efos import log, get_handlers, EFOS_SIG


class Barcode(object):
    def __init__(self, encoding, data):
        """

        :param encoding:
        :paramType: String
        :param data:
        :paramType data: String
        :return:
        """
        self._efos_sig = None
        self._is_efos = False
        self.type = encoding  #: QRCODE
        self.raw = data
        self.raw_data = data
        self._data = data

        self.cover_page = False
        self.merge = False
        self.new_page = False
        self.remove_page = False

        self._child_list = []

        self._parse_data()

    @property
    def efos_sig(self):
        """

        :return: The efos sig found
        """
        if self.is_efos:
            return self._efos_sig
        return None

    @property
    def is_efos(self):
        """ """
        return self._is_efos

    def _parse_data(self):
        """ """
        try:
            self._efos_sig = re.match(EFOS_SIG, self.raw_data).group()  # find the efos sig
            self.raw_data = self.raw_data.replace(self._efos_sig, "")
            self._is_efos = True
            log.debug('efos sig found: %s' % self.raw_data)
            self._parse_efos_data()
            self._parse_qs_data()
        except:
            pass
        log.debug('regex not found: %s' % self.raw_data)

    def _parse_efos_data(self):
        """ """
        self.cover_page = True if re.match("efos\d#[mnr]*[c][mnr]*#", self.efos_sig) else False
        self.merge = True if re.match("efos\d#[cnr]*[m][cnr]*#", self.efos_sig) else False
        self.new_page = True if re.match("efos\d#[mr]*[cn][mr]*#", self.efos_sig) else False
        self.remove_page = True if re.match("efos\d#[mn]*[cr][mn]*#", self.efos_sig) else False

    def _parse_qs_data(self):
        """ """
        self._data = urlparse.parse_qs(self.raw_data)
        for key, value in self._data.iteritems():
            self._data[key] = value[0]

    def push(self, barcode):
        """ """
        self._child_list.append(barcode)

    def pop(self):
        """ """
        return self._child_list.pop()

    @property
    def data(self):
        """ """
        ret_data = dict(self._data)
        for child in self._child_list:
            ret_data.update(child.data)
        return ret_data


class Page(object):
    """ """
    def __init__(self, page=None):
        """ """
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
        """ """
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
        """ """
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


class File(object):
    """ """
    def __init__(self, barcode, filename_format=None):
        self._filename_format = filename_format
        self.barcode = barcode
        self.pages = []
        self._filename = None
        self.valid_filename = False

    @property
    def page_count(self):
        """ """
        return len(self.pages)

    @property
    def basename(self):
        """ """
        return os.path.basename(self.get_filename())

    def get_filename(self):
        """ """
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
        """ """
        self.pages.append(page)

    def write(self, output):
        """ """
        pdf_file_writer = PdfFileWriter()
        for page in self.pages:
            log.debug('Adding page to file for writing')
            pdf_file_writer.addPage(page.page)
        pdf_file_writer.write(output)


class Parser(object):
    """ """
    def __init__(self, filename=None, options=None):
        """ """
        if not options:
            log.critical('No options passed to Parser')
            raise ValueError('No Options')
        self.options = options
        self.filename = filename
        log.debug('saved: %s and %s' % (self.filename, self.options))
        self.files = []
        log.debug('init file: %s' % self.files)
        self.handlers = get_handlers(self.options)
        log.debug('init finished')
        try:
            if not os.path.exists(self.filename):
                print "File path is invalid."
            elif not os.path.isfile(self.filename):
                print "File does not exist."
            elif not os.access(self.filename, os.R_OK):
                print "File cannot be read."
            else:
                self.pdf_file = PdfFileReader(self.filename, strict=False)
        except IOError as ex:
            print "I/O error({0}): {1}".format(ex.errno, ex.strerror)
            raise ex

    @property
    def file_count(self):
        """ """
        return len(self.files)

    def parse(self):
        """ """
        new_file = None
        for pdf_page in self.pdf_file.pages:
            page = Page(page=pdf_page)

            if page.is_efos:
                new_file = self.new_file(page.get_barcode())
                log.info("Creating page %s" % new_file.get_filename())
            elif new_file:
                new_file.add(page)
                log.debug("Adding page to %s" % new_file.get_filename())

    def process(self):
        """ """
        if len(self.files) == 0:
            log.warning("No efos files found")

        for file in self.files:
            for handler in self.handlers:
                handler.process(file)

        # self.archive_delete()

    def archive(self):
        for handler in self.handlers:
            handler.archive(self.filename)

    def delete(self):
        """ """
        # # After Parsing, Archive and Delete
        # if self.options.archive:
        #     archive_filename = os.path.join(self.options.archive, self.filename.replace(self.options.watch, "")[1:])
        #     if self.options.delete:
        #         log.info("Archiving file %s to %s" % (self.filename, archive_filename))
        #         log.info("Removing file %s" % (self.filename,))
        #         os.rename(self.filename, archive_filename)
        #     else:
        #         log.info("Archiving file %s to %s" % (self.filename, archive_filename))
        #         shutil.copy(self.filename, archive_filename)
        if self.options.delete:
            if os.path.exists(self.filename):
                os.remove(self.filename)
                log.info("Removing file %s" % (self.filename,))

    def new_file(self, barcode):
        """ """
        file = File(barcode, filename_format=self.get_filename_format())
        self.files.append(file)
        return file

    def get_filename_format(self):
        """ """
        return os.path.normpath(self.options.file_format)
