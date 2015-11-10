Installation
============

.. note::

    Currently there is no python package to install, but it is in the works.

Run as a daemon with Upstart:

1. Copy the source to /opt/efos
2. Create an upstart file located at ``/etc/init/efos.conf``

.. code-block:: bash

   start on runlevel [2345]
   stop on runlevel [016]

   chdir /opt/efos
   respawn
   setuid ubuntu
   setgid ubuntu
   exec python /opt/efos/file_processor.py -c /home/ubuntu/efos.conf

.. hint::

   ubuntu is the user efos will be run as. Rename this to your username.

3. Create a efos config file at ``~/efos.conf``. See :ref:`avalible options<options-label>` for more help.

.. code-block:: ini
   :caption: Example

   watch=/mnt/scans
   archive-path=/mnt/some/path/to/archive
   log-level=50

.. note::

   Will use the standard ``/etc/efos/efos.conf`` or maybe ``~/.efos/efos.config`` in later releases.
