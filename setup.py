#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
from setuptools import setup, find_packages

CLASSIFIERS = [
    'Development Status :: 1 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.6',
    'Topic :: System :: Filesystems',
]

with io.open('README.rst', 'r', encoding='utf8') as f:
    DESCRIPTION = f.read()

with io.open('HISTORY.rst', 'r', encoding='utf8') as f:
    HISTORY = f.read()

REQUIREMENTS = [
    "fs~=2.0.7",
    "requests"
]

setup(
    author="Henning Hraban Ramm, fiëé visuëlle",
    author_email="hraban@fiee.net",
    classifiers=CLASSIFIERS,
    description="SeaFile support for pyfilesystem2",
    entry_points={
        'fs.opener': 'seafile = seafile.opener:SeaFileOpener'
    },
    install_requires=REQUIREMENTS,
    license="MIT",
    long_description=DESCRIPTION + "\n" + HISTORY,
    name='fs.seafile',
    packages=find_packages(exclude=("tests",)),
    platforms=['any'],
    setup_requires=['nose'],
    # tests_require=['docker'],
    # test_suite='seafile.tests',
    # url="http://pypi.python.org/pypi/fs.seafile/",
    version="0.1.0"
)
