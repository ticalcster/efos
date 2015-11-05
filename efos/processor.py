import logging
import os
import time

import cherrypy

from ws4py.messaging import TextMessage
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from efos.parser import Parser

log = logging.getLogger('efos')


class EfosObserver(Observer):
    def on_thread_start(self):
        """ """
        log.info("Starting observer")
        super(EfosObserver, self).on_thread_start()

    def on_thread_stop(self):
        """ """
        log.info("Stopping observer")
        super(EfosObserver, self).on_thread_stop()


class ProcessEventHandler(PatternMatchingEventHandler):
    patterns = ('*pdf',)

    def __init__(self, options=None, **kwargs):
        """ """
        super(ProcessEventHandler, self).__init__(**kwargs)
        if not options:
            log.critical('No options passed to EventHandler')
            raise ValueError('No Options')
        self.options = options

    def on_created(self, event):
        """ """
        super(ProcessEventHandler, self).on_created(event)
        time.sleep(5)  # TODO: remove
        log.info(event.src_path)
        filename = event.src_path

        # timeout settings
        if self.options.delay > 0:
            time.sleep(self.options.delay)
        else:
            try_count = 0
            while try_count < 10:
                can_read = True
                if not os.path.exists(filename):
                    can_read = False
                elif not os.path.isfile(filename):
                    can_read = False
                elif not os.access(filename, os.R_OK):
                    can_read = False
                if can_read:
                    break
                time.sleep(1)
                try_count += 1
            log.debug('waited for %s seconds' % try_count)
        # Parse the file
        try:
            parser = Parser(filename=filename, options=self.options)
            parser.parse()
            parser.process()
        except Exception as ex:
            log.error("%s: Error: %s" % (filename, ex))

        # log.debug("source file: %s" % event.src_path)
        # log.debug("archive folder: %s" % self.options.archive)
        # log.debug(
        #     "archive file: %s" % os.path.join(self.options.archive, event.src_path.replace(self.options.archive, "")[1:]))


class Processor():
    def __init__(self, options=None):
        """ """
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
            os.makedirs(self.options.archive)

        if self.options.output and not os.path.isdir(self.options.output):
            log.info("Creating output directory %s.", self.options.output)
            os.makedirs(self.options.output)

    def run(self):
        """ """
        log.info("Processor watching %s." % self.options.watch)
        log.info("Output directory: %s" % self.options.output)
        log.info("Archive directory: %s" % self.options.archive)

        event_handler = ProcessEventHandler(options=self.options)
        observer = EfosObserver()
        observer.schedule(event_handler, self.options.watch, recursive=False)
        observer.start()
        return observer
        # try:
        #     while True:
        #         time.sleep(1)
        # except KeyboardInterrupt:
        #     observer.stop()
        # observer.join()
