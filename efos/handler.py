import os
from efos import log


class EfosHandler(object):
    def __init__(self, options=None):
        if not options:
            log.critical('No options passed to %s' % self.__class__.__name__)
            raise ValueError('No Options')
        self.options = options
        self.setup()

    def setup(self):
        pass

    @staticmethod
    def add_arguments(cap):
        pass

    def process(self, file):
        raise NotImplemented


class HttpHandler(EfosHandler):
    pass


class FileHandler(EfosHandler):
    def setup(self):
        if self.options.output:
            if not os.path.isabs(self.options.output):
                self.options.output = os.path.join(self.options.watch, self.options.output)

    @staticmethod
    def add_arguments(cap):
        cap.add_argument('-o', '--output', default="output", help='directory to output files')

    def process(self, file):
        try:
            f = open(file.get_filename(), 'wb')
            file.write(f)
        except IOError as ex:
            log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.strerror, 'args': ex.args})
