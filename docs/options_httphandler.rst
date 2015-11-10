url
^^^
The url to send the file.
If this option is left out no upload will be tried.

:Default: ``None``

http-timeout
^^^^^^^^^^^^
Time to wait to find the server.

:Default: ``10``

form-data
^^^^^^^^^
Additional form data to send to server.
In the config file you can specify multiple like so:

.. code-block:: ini

    form-data=id=something
    form-data=auth_token=somethingelse

:Default: ``None``

disable-http
^^^^^^^^^^^^
Will disable this file handler.

:Default: ``False``

file-form-name
^^^^^^^^^^^^^^
Uploads the file with a custom form param name.

:Default: ``file``
