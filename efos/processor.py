import logging
import os
import StringIO
import time
import json
import re

from wand.image import Image as WandImage
from PIL import Image as PILImage
from PyPDF2 import PdfFileReader, PdfFileWriter
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import zbar


log = logging.getLogger(__name__)


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
            self._efos_sig = re.match('^efos\d#', self.raw_data).group()
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
        #self.image.type = 'grayscale'
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
            #print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data

        # clean up
        del(image)
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


    def get_ascii(self,):
        # resize to: the max of the img is maxLen
        img = self.pil_image.copy()

        maxLen = 60.0   # default maxlen: 100px  # TODO: setting
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
                #string += "%s," % rgb
                ascii.write(color[int(rgb / 256.0 * 16)])
            ascii.write('|')
            ascii.write('\n')

        for w in xrange(width + 2):
            ascii.write('-')
        ascii.write('\n')

        return ascii.getvalue()


class File():
    def __init__(self, barcode):
        self.barcode = barcode
        self.pages = []

        log.info("File found: %s" % barcode.raw_data)

    def add(self, page):
        self.pages.append(page)

    def save(self, filename=None, path=None):
        pdf_file_writer = PdfFileWriter()
        for page in self.pages:
            pdf_file_writer.addPage(page.page)
        with open("%s.pdf" % self.barcode.data.get('eid'), 'wb') as f:
            pdf_file_writer.write(f)


class Parser():
    def __init__(self, filename=None):
        self.files = []
        self.filename = filename


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

    def parse(self):
        new_file = None
        for pdf_page in self.pdf_file.pages:
            page = Page(page=pdf_page)

            if page.is_efos:
                new_file = self.new_file(page.get_barcode())
            elif file:
                new_file.add(page)

        for pdf_file in self.files:
            pdf_file.save()

    def new_file(self, barcode):
        file = File(barcode)
        self.files.append(file)
        return file


class ProcessEventHandler(PatternMatchingEventHandler):
    patterns = ('*pdf',)

    def on_created(self, event):
        super(ProcessEventHandler, self).on_created(event)
        time.sleep(1)
        log.info(event.src_path)
        parser = Parser(filename=event.src_path)
        parser.parse()


class Processor():
    def __init__(self, watch=None, archive=None, output=None):
        self.watch_directory = watch
        self.archive_directory = archive
        self.output = output
        log.info("Processor created.")

        if not os.path.isdir(self.watch_directory):
            log.info("Creating directory %s.", self.watch_directory)
            os.makedirs(self.watch_directory)

    def run(self):
        log.info("Processor watching %s." % self.watch_directory)
        event_handler = ProcessEventHandler()
        observer = Observer()
        observer.schedule(event_handler, self.watch_directory, recursive=False)
        observer.start()

