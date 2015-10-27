import StringIO
import os
import requests
from collections import OrderedDict

from efos import log


class EfosHandler(object):
    def __init__(self, options=None):
        """ """
        if not options:
            log.critical('No options passed to %s' % self.__class__.__name__)
            raise ValueError('No Options')
        self.options = options
        self.setup()

    def setup(self):
        """Called after __init__(). Used to perform global handler actions."""
        pass

    @staticmethod
    def add_arguments(cap):
        """Called durning server start. Used to add options to the config file/args/env."""
        pass

    def process(self, file):
        """
        Function run on each parsed file.

        :param file: :class:`efos.parser.File`
        """
        log.warning('%s process not implemented' % self.__class__.__name__)


class HttpHandler(EfosHandler):
    @staticmethod
    def add_arguments(cap):
        cap.add_argument('-u', '--url', default=None, help='url to upload files')
        cap.add_argument('--http-timeout', default=10, help='time to wait for server to respond')
        cap.add_argument('--form-data', default=None, action="append", help='additional form data to send to server')
        cap.add_argument('--disable-http', action="store_true", help="Will disable the FileHandler")
        cap.add_argument('--file-form-name', default="file", help="POST param name for the uploaded file")

    def get_form_data(self, file):
        """
        Returns the combined form data from Options and the scanned efos barcode.

        :param file: :class:`efos.parser.File`
        :return:
        """
        form_data = {}
        if self.options.form_data:
            for option in self.options.form_data:
                # TODO: need to catch an error here on the split
                key, value = option.split('=')[:2]  # the args for options are and array of key=value strings
                form_data.update({key: value})
        form_data.update(file.barcode.data)  # merge the barcode data
        return dict(OrderedDict((form_data.iteritems())))

    def process(self, file):
        if self.options.url:
            log.info("Uploading %(filename)s to %(url)s" % {'filename': file.get_filename(), 'url': self.options.url})
            try:
                f = StringIO.StringIO()
                file.write(f)
                files = {self.options.file_form_name: (file.get_filename(), f.getvalue(), 'application/pdf', {})}
                log.debug(self.get_form_data(file))
                r = requests.post(self.options.url, data=self.get_form_data(file), files=files)

                if r.status_code == 200:
                    log.info("file uploaded!")
                else:
                    log.warning("Server responded with status code %s [%s]" % (r.status_code, r.text))

            except IOError as ex:
                log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.message, 'args': ex.args})
            except requests.exceptions.ConnectionError as ex:
                log.error("Could not contact server")
            except requests.exceptions.Timeout as ex:
                log.error("Request timed out")
            except Exception as ex:
                log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.message, 'args': ex.args})


class FileHandler(EfosHandler):
    """FileHanlder is used to save the parsed files to a file system directory."""

    def setup(self):
        if self.options.output:
            if not os.path.isabs(self.options.output):
                self.options.output = os.path.join(self.options.watch, self.options.output)

    @staticmethod
    def add_arguments(cap):
        cap.add_argument('-o', '--output', default="output", help='directory to output files')
        cap.add_argument('--disable-output', action="store_true", help="Will disable the FileHandler.")

    def process(self, file):
        if self.options.disable_output:
            log.debug("FileHandler has been disabled.")
            return

        log.info("Saving %(filename)s" % {'filename': file.get_filename()})
        try:
            f = open(file.get_filename(), 'wb')
            file.write(f)
            f.close()
        except IOError as ex:
            log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.strerror, 'args': ex.args})
