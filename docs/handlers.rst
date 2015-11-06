Handlers
========

Handlers define what to do with the parsed pdf files.
Currently two hanlders are built in (third is in progress).
Each handler has its own settings and :py:meth:`~efos.handlers.EfosHander.process` method to do some kind of operation on the file.

Builtin Handlers
----------------

FileHandler
***********

This is the simplest handler. It will save the parsed file to the file system.

HttpHandler
***********

This handler will post the file to a web server.

DropboxHandler
**************

Coming soon.

Write Your Own
--------------

You can write your own handler to use. Check out :class:`efos.handler.EfosHanlder` and the :ref:`handlers<option-handlers-label>` config option.
