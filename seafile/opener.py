# coding: utf-8
"""Defines the SeaFile opener."""

from __future__ import absolute_import
from __future__ import unicode_literals

from fs.opener.base import Opener

__author__ = "Henning Hraban Ramm <hraban@fiee.net>"


class SeaFileOpener(Opener):
    protocols = ['seafile']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        from .seafile import SeaFile

        seafile_host, _, dir_path = parse_result.resource.partition('/')
        seafile_host, _, seafile_port = seafile_host.partition(':')
        seafile_port = int(seafile_port) if seafile_port.isdigit() else 80
        seafile_scheme = 'http' if seafile_port != 443 else 'https'

        return SeaFile(
            url='{}://{}:{}'.format(seafile_scheme, seafile_host, seafile_port),
            login=parse_result.username,
            password=parse_result.password,
            root=dir_path,
        )
