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


License
-------

This module is published under the MIT license.


Contact
-------

| fiëé visuëlle
| Henning Hraban Ramm
| https://www.fiee.net