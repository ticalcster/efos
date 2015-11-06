Options
=======

.. code-block:: ini
   :caption: efos.conf

    log-level=50

Base Options
------------

archive
^^^^^^^
default="archive", help='directory to archive files')

config
^^^^^^
path to config file

delete
^^^^^^
delete files after processing

delay
^^^^^
added a delay between getting notified and processing the file

file-format
^^^^^^^^^^^
filename format from kwargs in QRCode


.. _option-handlers-label:

handlers
^^^^^^^^
default=['efos.handler.FileHandler', 'efos.handler.HttpHandler'], help='handlers to use when processing parsed files

log-level
^^^^^^^^^
default=11, type=int, help='logging level [1-50+]

port
^^^^
default=8081, type=int, help='web server port


watch
^^^^^
required=True, help='directory to watch for files

FileHandler Options
-------------------

.. include:: options_filehandler.rst

HttpHandler Options
-------------------

.. include:: options_httphandler.rst
