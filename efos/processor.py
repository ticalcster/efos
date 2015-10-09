import logging
import os
import StringIO
import time
import json
import re
import shutil

import cherrypy
from ws4py.messaging import TextMessage
from wand.image import Image as WandImage
from PIL import Image as PILImage
from PyPDF2 import PdfFileReader, PdfFileWriter
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import zbar

log = logging.getLogger(__name__)

EFOSSIG = '^efos\d#'


class Barcode():
    def __init__(self, encoding, data):
        self._efos_sig = None
        self.type = encoding
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
            return True
        except:
            pass
        log.error('Reg not found: %s' % self.raw_data)
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

    @property
    def page_count(self):
        return len(self.pages)

    @property
    def basename(self):
        return os.path.basename(self.filename)

    @property
    def filename(self):
        return self._filename_format % self.barcode.data

    def add(self, page):
        self.pages.append(page)

    def save(self, output):
        f = None
        if isinstance(output, str):
            f = open(output, 'wb')
        else:
            f = output
        self.write(f)

    def write(self, output):
        pdf_file_writer = PdfFileWriter()
        for page in self.pages:
            pdf_file_writer.addPage(page.page)
        pdf_file_writer.write(output)


class Parser():
    def __init__(self, filename=None, options=None):
        if not options:
            log.critical('No options passed to Processor')
            raise ValueError('No Options')
        self.options = options
        self.filename = filename
        self.files = []

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
            elif file:
                new_file.add(page)

    def process(self):
        if self.options.output:
            self.save_output()

        self.archive_delete()

    def save_output(self):
        for pdf_file in self.files:
            pdf_file.save(pdf_file.filename)

    def archive_delete(self):
        # After Parsing, Archive and Delete
        if self.options.archive:
            archive_filename = os.path.join(self.options.archive, self.filename.replace(self.options.watch, "")[1:])
            if self.options.delete:
                os.rename(self.filename, archive_filename)
            else:
                shutil.copy(self.filename, archive_filename)
        elif self.options.delete:
            if os.path.exists(self.filename):
                os.remove(self.filename)

    def new_file(self, barcode):
        file = File(barcode, filename_format=self.get_filename_format())
        self.files.append(file)
        return file

    def get_filename_format(self):
        return os.path.normpath(os.path.join(self.options.output, self.options.file_format))


class ProcessEventHandler(PatternMatchingEventHandler):
    patterns = ('*pdf',)

    def __init__(self, options=None, **kwargs):
        super(ProcessEventHandler, self).__init__(**kwargs)
        if not options:
            log.critical('No options passed to Processor')
            raise ValueError('No Options')
        self.options = options

        log.info("Output directory: %s" % self.options.output)
        log.info("Archive directory: %s" % self.options.archive)

    def on_created(self, event):
        super(ProcessEventHandler, self).on_created(event)
        time.sleep(1)
        log.info(event.src_path)
        filename = event.src_path

        # Parse the file
        parser = Parser(filename=filename)
        parser.parse()

        # log.debug("source file: %s" % event.src_path)
        # log.debug("archive folder: %s" % self.options.archive)
        # log.debug(
        #     "archive file: %s" % os.path.join(self.options.archive, event.src_path.replace(self.options.archive, "")[1:]))


class Processor():
    def __init__(self, options=None):
        if not options:
            log.critical('No options passed to Processor')
            raise ValueError('No Options')
        self.options = options

        log.info("Processor created.")

        if not os.path.isdir(self.options.watch):
            log.info("Creating watch directory %s.", self.options.watch)
            os.makedirs(self.options.watch)

        if self.options.archive and not os.path.isdir(self.options.archive):
            log.info("Creating archive directory %s.", self.options.archive)
            os.makedirs(self.options.watch)

    def run(self):
        log.info("Processor watching %s." % self.options.watch)
        event_handler = ProcessEventHandler(options=self.options)
        observer = Observer()
        observer.schedule(event_handler, self.options.watch, recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
