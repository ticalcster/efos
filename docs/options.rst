Options
=======

.. code-block:: ini
   :caption: efos.conf

    log-level=50

Base Options
------------

archive
^^^^^^^
Tells the :py:class:`~efos.parser.Parser` whether or not to archive the original file.

:Default: ``True``

config
^^^^^^
Path to a config file.

delete
^^^^^^
Tells the :py:class:`~efos.parser.Parser` whether or not to delete the original file after processing.

:Default: ``True``

delay
^^^^^
Adds a delay (seconds) between getting notified of a new file and processing of the file.
If the delay is 0 the :py:class:`~efos.processor.Processor` will check 6 times if the file exists and can be opened.
Between each try there is a 1 second delay.
That gives the scanner up to six seconds to copy the file to the folder.

:Default: ``0``

filename-format
^^^^^^^^^^^^^^^
This is how efos should name each parsed file. It uses pythons old % formatting with the barcode data.

.. code-block:: python

   filename = self.options.filename_format % self.barcode.data

.. note::

   This is probably going to change in a later release to the new formatting style.


:Default: ``%(filename)s``


.. _option-handlers-label:

handlers
^^^^^^^^
Defines the handlers to use when processing files.
Each handler has a :py:meth:`~efos.handler.EfosHandler.process` method for the parsed file.
The :py:meth:`~efos.handler.EfosHandler.archive` method is used to archive the orignal file.

:Default: ``['efos.handler.FileHandler', 'efos.handler.HttpHandler']``

log-level
^^^^^^^^^
Pythons logging level.

:Default: ``11``

port
^^^^
Webserver port.

:Default: ``8081``

.. _option-watch-label:

watch
^^^^^
This tells efos which director to watch for changes.

:Required: ``True``

DropboxHandler Options
----------------------

.. include:: options_dropboxhandler.rst

FileHandler Options
-------------------

.. include:: options_filehandler.rst

HttpHandler Options
-------------------

.. include:: options_httphandler.rst
