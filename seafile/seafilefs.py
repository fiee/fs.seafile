# -*- coding: utf-8 -*-
import os
from fs.base import FS
from fs.enums import ResourceType
from fs.errors import FileExpected, ResourceNotFound
from fs.info import Info
from fs.mode import Mode
from fs.subfs import SubFS
from fs.time import datetime_to_epoch, epoch_to_datetime
from .seafileapi import Connection
# from seafile.files import DownloadError, FileMetadata, FolderMetadata, WriteMode
# from seafile.exceptions import ApiError
from fs_s3fs._s3fs import S3File


class SeafileFile(S3File):
    """
    Proxy for a Seafile file, backed by a temporary local file.
    Inherits without changes from `fs_s3fs._s3fs.S3File`
    by Will McGugan, MIT license,
    see https://github.com/PyFilesystem/s3fs
    """
    pass


class SeafileFS(FS):
    def __init__(self, **kwargs):
        """
        kwargs = kwargs of `seafileapi.Connection`:
        'server': including protocol and port, e.g. https://cloud.seafile.com:9999
        'username': email address
        'password': ;)
        """
        super().__init__()
        self.connection = Connection(**kwargs)
        self.connection.connect()
        _meta = self._meta = {
            "case_insensitive": False,
            "invalid_path_chars": ":",  # not sure what else
            "max_path_length": None,  # don't know what the limit is
            "max_sys_path_length": None,  # there's no syspath
            "network": True,
            "read_only": False,
            "supports_rename": False  # since we don't have a syspath...
        }
        self.libraries = {}
        self._get_libraries()

    def __repr__(self):
        return "<SeafileFS>"

    """
    The following methods MUST be implemented in a PyFilesystem interface.

    (√) getinfo() Get info regarding a file or directory.
    √ listdir() Get a list of resources in a directory.
    √ makedir() Make a directory.
    openbin() Open a binary file.
    √ remove() Remove a file.
    √ removedir() Remove a directory.
    setinfo() Set resource information.
    """

    def _get_libraries(self):
        libs = self.connection.library_list()
        for lib in libs:
            # find libraries by id or name
            self.libraries[lib['id']] = lib
            self.libraries[lib['name']] = lib

    def _get_lib_id_and_path(self, path):
        parts = list(e for e in path.split('/') if e)
        lib = parts[0]
        if lib in self.libraries:
            return self.libraries[lib]['id'], '/'.join(parts[1:])
        raise ResourceNotFound(path, None, 'Unknown library "%s"' % lib)

    def _get_lib_id(self, path):
        return self._get_lib_id_and_path(path)[0]

    def getinfo(self, path, namespaces=None):
        # namespaces: basic, details
        # TODO: access, history, comments, stars
        namespaces = namespaces or ()
        _path = self.validatepath(path)
        if not _path.startswith('/'):
            _path = '/' + _path
        _lib_id, _subpath = self._get_lib_id_and_path(_path)
        _parts = list(e for e in _path.split('/') if e)
        info_dict = {
            "basic": {
                "name": "",
                "is_dir": True
            },
            "details": {
                "accessed": None,
                "created": None,
                "metadata_changed": None,
                "modified": None,
                "size": 0,
                "type": ResourceType.directory
            }
        }

        if len(_parts) == 1:  # library only
            info = self.connection.library_info(_lib_id)
            info_dict['basic']['name'] = info['name']
            info_dict['details']['modified'] = info['mtime']
            info_dict['details']['size'] = info['size']
        elif _path == '/':
            # Root doesn’t really exist in SeaFile
            pass
        else:
            info = self.connection.file_info(_lib_id, '/'.join(_parts[1:]))
            info_dict['basic']['name'] = info['name']
            info_dict['basic']['is_dir'] = info['type'] != 'file'
            info_dict['basic']['id'] = info['id']
            info_dict['details']['modified'] = info['mtime']
            info_dict['details']['size'] = info['size']
            if info['type'] == 'file':
                info_dict['details']['type'] = ResourceType.file
        return Info(info_dict)

    def setinfo(self, path, info):
        # seafile doesn't support changing any of the metadata values
        # except name - maybe include comments, stars, permissions?
        pass

    def listdir(self, path):
        lib_id, path = self._get_lib_id_and_path(path)
        return self.connection.dir_list(lib_id, path)

    def makedir(self, path, permissions=None, recreate=False):
        # TODO: set permissions, check for errors
        lib_id, path = self._get_lib_id_and_path(path)
        self.connection.dir_create(lib_id, path)
        return SubFS(self, path)

    def remove(self, path):
        lib_id, path = self._get_lib_id_and_path(path)
        self.connection.file_delete(lib_id, path)

    def removedir(self, path):
        lib_id, path = self._get_lib_id_and_path(path)
        self.connection.dir_delete(lib_id, path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        # inherited from fs_s3fs
        _mode = Mode(mode)
        _mode.validate_bin()
        self.check()
        _path = self.validatepath(path)
        _key = self._path_to_key(_path)

        if _mode.create:

            def on_close_create(sffile):
                """Called when the SeaFile file closes, to upload data."""
                try:
                    sffile.raw.seek(0)
                    with s3errors(path):
                        self.connection.upload_fileobj(
                            sffile.raw, self._bucket_name, _key
                        )
                finally:
                    sffile.raw.close()

            try:
                dir_path = dirname(_path)
                if dir_path != '/':
                    _dir_key = self._path_to_dir_key(dir_path)
                    self._get_object(dir_path, _dir_key)
            except errors.ResourceNotFound:
                raise errors.ResourceNotFound(path)

            try:
                info = self._getinfo(path)
            except errors.ResourceNotFound:
                pass
            else:
                if _mode.exclusive:
                    raise errors.FileExists(path)
                if info.is_dir:
                    raise errors.FileExpected(path)

            sffile = SeafileFile.factory(path, _mode, on_close=on_close_create)
            if _mode.appending:
                try:
                    with s3errors(path):
                        self.connection.download_fileobj(
                            self._bucket_name, _key, sffile.raw
                        )
                except errors.ResourceNotFound:
                    pass
                else:
                    sffile.seek(0, os.SEEK_END)

            return sffile

        if self.strict:
            info = self.getinfo(path)
            if info.is_dir:
                raise errors.FileExpected(path)

        def on_close(sffile):
            """Called when the S3 file closes, to upload the data."""
            try:
                if _mode.writing:
                    sffile.raw.seek(0, os.SEEK_SET)
                    with s3errors(path):
                        self.connection.upload_fileobj(
                            sffile.raw, self._bucket_name, _key
                        )
            finally:
                sffile.raw.close()

        sffile = SeafileFile.factory(path, _mode, on_close=on_close)
        with s3errors(path):
            self.connection.download_fileobj(
                self._bucket_name, _key, sffile.raw
            )
        sffile.seek(0, os.SEEK_SET)
        return sffile
