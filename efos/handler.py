import StringIO
import os
import requests

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
    @staticmethod
    def add_arguments(cap):
        cap.add_argument('-u', '--url', default=None, help='url to upload files')
        cap.add_argument('--http-timeout', default=10, help='url to upload files')
        cap.add_argument('--form-data', default=None, help='url to upload files')

    def process(self, file):
        if self.options.url:

            log.info("Uploading %(filename)s to %(url)s" % {'filename': file.get_filename(), 'url': self.options.url})
            try:
                f = StringIO.StringIO()
                file.write(f)
                files = {'file': ('something.pdf', f.getvalue())}
                r = requests.post(self.options.url, files=files, timeout=self.options.http_timeout)
                if r.status_code == 200:
                    log.info("file uploaded!")
                else:
                    log.warning("Server responded with status code %s" % r.status_code)

            except IOError as ex:
                log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.strerror, 'args': ex.args})
            except requests.exceptions.ConnectionError as ex:
                log.error("Could not contact server")
            except requests.exceptions.Timeout as ex:
                log.error("Request timed out")
            except Exception as ex:
                log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.strerror, 'args': ex.args})


class FileHandler(EfosHandler):
    def setup(self):
        if self.options.output:
            if not os.path.isabs(self.options.output):
                self.options.output = os.path.join(self.options.watch, self.options.output)

    @staticmethod
    def add_arguments(cap):
        cap.add_argument('-o', '--output', default="output", help='directory to output files')

    def process(self, file):
        log.info("Saving %(filename)s" % {'filename': file.get_filename()})
        try:
            f = open(file.get_filename(), 'wb')
            file.write(f)
        except IOError as ex:
            log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.strerror, 'args': ex.args})
