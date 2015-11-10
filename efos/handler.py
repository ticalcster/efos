import StringIO
import os
import requests
import shelve
import shutil
from collections import OrderedDict

import dropbox
from dropbox.exceptions import AuthError, ApiError

from efos import log


class EfosHandler(object):
    def __init__(self, options=None):
        """ """
        log.debug('%s Setup' % self.__class__.__name__)
        if not options:
            log.critical('No options passed to %s' % self.__class__.__name__)
            raise ValueError('No Options')
        self.options = options
        self.setup()

    @staticmethod
    def add_arguments(cap):
        """Called durning server start. Used to add options to the config file/args/env."""
        pass

    def setup(self):
        """Called after ``__init__``. Used to perform global handler actions."""
        pass

    def process(self, file):
        """
        Function run on each parsed file.

        :param file: :class:`~efos.parser.File`
        """
        log.debug('%s process not implemented' % self.__class__.__name__)

    def archive(self, src_filename):
        """
        Function run on the source pdf after parsing is complete.

        :param src_filename: ``string``
        """
        log.debug('%s archive not implemented' % self.__class__.__name__)


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

        :param file: :py:class:`~efos.parser.File`
        :return: ``dict``
        """
        form_data = {}
        if self.options.form_data:
            for option in self.options.form_data:
                # TODO: need to catch an error here on the split
                key, value = option.split('=')[:2]  # the args for options are and array of key=value strings
                form_data.update({key: value})
        form_data.update(file.barcode.data)  # merge the barcode data
        return OrderedDict(sorted(form_data.iteritems()))

    def process(self, file):
        if self.options.url:
            log.info("Uploading %(filename)s to %(url)s" % {'filename': file.get_filename(), 'url': self.options.url})
            try:
                f = StringIO.StringIO()
                file.write(f)
                files = {'file': (os.path.basename(file.get_filename()), f.getvalue(), 'application/pdf', {})}
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

    @staticmethod
    def add_arguments(cap):
        cap.add_argument('-o', '--output-path', default="output", help='directory to output files')
        cap.add_argument('--archive-path', default="archive", help='directory to archive files')
        cap.add_argument('--disable-output', action="store_true", help="Will disable the FileHandler.")

    def setup(self):
        log.debug('%s Setup' % self.__class__.__name__)

        if not os.path.isabs(self.options.output_path):
            self.options.output_path = os.path.join(self.options.watch, self.options.output_path)

        if not os.path.isabs(self.options.archive_path):
            self.options.archive_path = os.path.join(self.options.watch, self.options.archive_path)

        if self.options.archive and not os.path.isdir(self.options.archive_path):
            log.info("Creating archive directory %s.", self.options.archive_path)
            os.makedirs(self.options.archive_path)

        if not self.options.disable_output and not os.path.isdir(self.options.output_path):
            log.info("Creating output directory %s.", self.options.output_path)
            os.makedirs(self.options.output_path)

    def process(self, file):
        if self.options.disable_output:
            log.debug("FileHandler has been disabled.")
            return

        log.info("Saving %(filename)s" % {'filename': file.get_filename()})
        full_path = self.options.output_path % file.barcode.data
        full_path = os.path.normpath(os.path.join(full_path, file.get_filename()))
        try:
            f = open(full_path, 'wb')
            file.write(f)
            f.close()
        except IOError as ex:
            log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.strerror, 'args': ex.args})

    def archive(self, src_file):
        try:
            shutil.copy(src_file, self.options.archive_path)
        except Exception as ex:
            log.error(ex)


class DropboxHandler(EfosHandler):
    # todo: not sure if this is how it should be handled, maybe put in init.
    dbx = None
    dbx_key = None
    dbx_secret = None
    dbx_token = None
    dbx_user = None

    @staticmethod
    def add_arguments(cap):
        cap.add_argument('--dbx-key', default=None, help='Dropbox Application key')
        cap.add_argument('--dbx-secret', default=None, help='Dropbox Application secret')
        cap.add_argument('--dbx-token', default=None, help='Application access token')
        cap.add_argument('--dbx-path', default='/output', help='File path in Dropbox account')
        cap.add_argument('--dbx-archive', default='/archive', help='File path in Dropbox account')
        cap.add_argument('--dbx-autorename', action='store_true', default=True, help='Rename file if it already exists')
        # todo: add some kind of encryption to the tokens

    def setup(self):
        log.debug('%s Setup' % self.__class__.__name__)
        self.dbx_key = self.options.dbx_key
        self.dbx_secret = self.options.dbx_secret
        self.dbx_token = self.get_token()

        try:
            self.dbx = dropbox.Dropbox(self.dbx_token)
            self.dbx_user = self.dbx.users_get_current_account()
            log.info(self.dbx_user.name.display_name)
        except AuthError as ex:
            log.warning('Dropbox Auth Error')

    def get_token(self):
        if self.options.dbx_token:
            return self.options.dbx_token

        store = shelve.open('dbx.dat')
        if 'token' in store:
            token = store['token']  # Should we encrypt this? the source is open though
            store.close()
            return token

        token = self.generate_token()
        store['token'] = token
        store.close()
        return token

    def generate_token(self):
        if not (self.dbx_key and self.dbx_secret):
            log.warning('Must have a key and secret to generate a token.')
            return

        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(self.dbx_key, self.dbx_secret)
        authorize_url = flow.start()

        # Have the user sign in and authorize this token
        authorize_url = flow.start()
        print('1. Go to: %s' % authorize_url)
        print('2. Click "Allow" (you might have to log in first)')
        print('3. Copy the authorization code.')
        code = raw_input("Enter the authorization code here: ").strip()

        # This will fail if the user enters an invalid authorization code
        try:
            access_token, user_id = flow.finish(code)
            print('Your token is: %s' % access_token)
            print('It is stored in dbx.dat')
            print('You may also put it in the config options.')
            return access_token
        except Exception as ex:
            print('Looks like that was an incorrect code.')

    def process(self, file):
        log.info('Uploading %(filename)s to Dropbox.' % {'filename': file.get_filename()})

        try:
            f = StringIO.StringIO()
            file.write(f)
            f.seek(0)  # not sure why but dropbox would fail with out that, it shouldn't ne read at all.
            upload_path = self.options.dbx_path % file.barcode.data
            try:
                meta_data = self.dbx.files_upload(f, file.get_filename(), autorename=self.options.dbx_autorename)
                log.info("File saved to Dropbox. REV: %s", meta_data.name)
            except ApiError as ex:
                log.error(ex)

        except IOError as ex:
            log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.message, 'args': ex.args})
        except Exception as ex:
            log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.message, 'args': ex.args})
            log.error(ex)

    def archive(self, src_file):
        log.info('Archiving  %(filename)s to Dropbox.' % {'filename': os.path.basename(src_file)})
        try:
            f = open(src_file, 'r')
            filename = os.path.join(self.options.dbx_archive, os.path.basename(src_file))
            try:
                meta_data = self.dbx.files_upload(f, filename, autorename=self.options.dbx_autorename)
            except ApiError as ex:
                log.error(ex)
            f.close()
        except IOError as ex:
            log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.message, 'args': ex.args})
        except Exception as ex:
            log.error("%(type)s: %(msg)s" % {'type': type(ex).__name__, 'msg': ex.message, 'args': ex.args})
            log.error(ex)
