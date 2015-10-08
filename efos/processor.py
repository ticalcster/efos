import logging
import os
import StringIO
import time

from wand.image import Image as WandImage
from PIL import Image as PILImage
from PyPDF2 import PdfFileReader, PdfFileWriter
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import zbar


log = logging.getLogger(__name__)


class Page():
    def __init__(self, page=None):
        self.page = page
        self._page_stream = None
        self._image_stream = None

        # Convert Image to B/W
        pil = PILImage.open(self.get_image_stream()).convert('L')
        width, height = pil.size
        raw = pil.tostring()


        # create a reader
        scanner = zbar.ImageScanner()

        # configure the reader
        scanner.parse_config('enable')

        # wrap image data
        image = zbar.Image(width, height, 'Y800', raw)

        # scan the image for barcodes
        scanner.scan(image)
        # extract results
        for symbol in image:
        # do something useful with results
            print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data

        # clean up
        del(image)

    def get_page_stream(self):
        if not self._page_stream:
            self._page_stream = StringIO.StringIO()
            pdf_file_writer = PdfFileWriter()
            pdf_file_writer.addPage(self.page)
            pdf_file_writer.write(self._page_stream)
        return self._page_stream

    def get_image_stream(self):
        if not self._image_stream:
            # Convert pdf file to image
            self._image_stream = StringIO.StringIO()
            pdf_image = WandImage(blob=self.get_page_stream().getvalue())
            self.image = pdf_image.convert('png')
            #self.image.type = 'grayscale'
            self.image.save(file=self._image_stream)
        return self._image_stream




class File():
    def __init__(self):
        pass


class Parser():
    def __init__(self, filename=None):
        self.filename = filename
        self.files = []
        log.info("Parsing %s" % self.filename)

    def parse(self):
        pdf_file = PdfFileReader(self.filename)
        for pdf_page in pdf_file.pages:
            page = Page(page=pdf_page)


        #outfile = PdfFileWriter()
        #outfile.addPage(pdf_file.getPage(1))
        #outfile.write(output_page)


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
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
