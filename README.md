``fs.seafile`` is a SeaFile driver for PyFilesystem2.


Supported Python versions
-------------------------

- Python 2.7
- Python 3.6

Usage
-----

Use the ``fs.open_fs`` method with the ``seafile://`` protocol:

.. code:: python

    >>> import fs
    >>> handle = fs.open_fs('seafile://user@example.com:password@cloud.seafile.com')

or use the public constructor of the ``SeaFile`` class:

.. code:: python

    >>> from seafile.seafile import SeaFile
    >>> url = 'https://cloud.seafile.com'
    >>> root = '/My Library'
    >>> handle = SeaFile(url, login='user@example.com', password='password', root)
    >>> handle.makedir('foo')
    >>> print(handle.listdir('.'))
    ....

Use the library’s name or ID as root directory; in case the name’s not
unique, you must use the ID.
It doesn’t matter if the library belongs to you or is shared with you.
There can’t be any files or "real" directories at root, only libraries!
`makedir` at root is translated into "make a new library".

These are valid paths:

    /My Library/SeaFile Manual.rtf
    /b8c8eeaf-a62f-4ece-a2cb-e1c67f49f881/IMG_1234.jpg
    /Some Shared Stuff/subdir/another sub/my file.txt

These are invalid paths:

    /Somefile.doc
    My Library/SeaFile Manual.rtf


Repository
----------

- https://github.com/fiee/fs.seafile


Issue tracker
-------------

- https://github.com/fiee/fs.seafile/issues


Tests
-----

(not yet)
- https://travis-ci.org/fiee/fs.seafile/builds


Author and contributors
-----------------------

- Henning Hraban Ramm
- SeafileFile/openbin code inherited from [S3FS](https://github.com/PyFilesystem/s3fs) by Will McGaugan
- other code partially copied from [DropboxFS](https://github.com/rkhwaja/fs.dropboxfs/) by Rehan Khwaja


License
-------

This module is published under the MIT license.


Contact
-------

| fiëé visuëlle
| Henning Hraban Ramm
| https://www.fiee.net
