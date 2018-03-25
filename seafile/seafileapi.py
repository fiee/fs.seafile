#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import requests

# logging.basicConfig(
#    level=logging.INFO,
#    format='%(levelname)-5s\t%(module)s.%(funcName)s#%(lineno)d\t%(message)s')

STATUS_CODES = {
    200: 'OK',
    201: 'CREATED',
    202: 'ACCEPTED',
    301: 'MOVED_PERMANENTLY',
    400: 'BAD_REQUEST',
    403: 'FORBIDDEN',
    404: 'NOT_FOUND',
    405: '???405',
    409: 'CONFLICT',
    429: 'TOO_MANY_REQUESTS',
    440: 'REPO_PASSWD_REQUIRED',
    441: 'REPO_PASSWD_MAGIC_REQUIRED',
    500: 'INTERNAL_SERVER_ERROR',
    520: 'OPERATION_FAILED'
}

# url = 'https://seacloud.cc/api2/auth-token/'
# values = {'username': 'demo@seafile.com',
#           'password': 'demo'}
# data = urllib.urlencode(values)
# req = urllib2.Request(url, data)
# response = urllib2.urlopen(req)
# the_page = response.read()
# token = json.loads(the_page)['token']


class Connection:

    defaults = {
        'server': 'https://seacloud.cc',
        'username': 'demo@seafile.com',
        'password': 'demo',
        'auth_token': None,
        'headers': {'Accept': 'application/json; charset=utf-8; indent=4'},
        'open': False
    }

    def _update(self, **kwargs):
        for key, val in self.defaults.items():
            if key in kwargs:
                val = kwargs[key]
            self.__dict__[key] = val

    def __init__(self, **kwargs):
        """
        kwargs:
        'server': including protocol and port
        'username': email address
        'password': ;)
        'auth_token': in case you already got that, then username and password are obsolete
        'headers': default should be good
        """
        self._update(**kwargs)
        if 'auth_token' in kwargs and kwargs['auth_token']:
            # no need to 'connect'
            self.headers['Authorization'] = 'Token ' + kwargs['auth_token']
            self.open = True  # TODO: check?

    def connect(self, **kwargs):
        kwargs.update(self.__dict__)
        data = {
            'username': kwargs['username'],
            'password': kwargs['password']
            }
        logging.debug('Connect as %s' % data)
        self._request = requests.post(
            kwargs['server'] + '/api2/auth-token/',
            data=data,
            headers=kwargs['headers'])
        logging.info('CONNECT Status %d, Headers %s' % (self._request.status_code, self._request.headers))
        try:
            self.auth_token = self._request.json()['token']
            self.headers['Authorization'] = 'Token ' + self.auth_token
            logging.debug('Headers: %s' % self.headers)
            self.open = True
        except KeyError as e:
            logging.error(e)
            self.open = False
        return self.open

    def get_request(self, path='', params={}):
        if not self.open:
            self.connect()
        r = requests.get(
            self.server + path,
            params=params,
            headers=self.headers)
        logging.info('GET %d %s %s' % (r.status_code, r.url, r.headers))
        r.raise_for_status()
        return r

    def post_request(self, path='', params={}):
        if not self.open:
            self.connect()
        r = requests.post(
            self.server + path,
            data=params,
            headers=self.headers)
        logging.info('POST %d %s %s' % (r.status_code, r.url, r.headers))
        r.raise_for_status()
        return r

    def put_request(self, path='', params={}):
        if not self.open:
            self.connect()
        r = requests.put(
            self.server + path,
            data=params,
            headers=self.headers)
        logging.info('PUT %d %s %s' % (r.status_code, r.url, r.headers))
        r.raise_for_status()
        return r

    def delete_request(self, path=''):
        if not self.open:
            self.connect()
        r = requests.delete(
            self.server + path,
            headers=self.headers)
        logging.info('DEL %d %s %s' % (r.status_code, r.url, r.headers))
        r.raise_for_status()
        return r

    def server_version(self):
        """
        Return server version as a string.
        """
        return self.get_request('/api2/server-info/').json()['version']

    def account_info(self, email=None):
        """
        Return account info for current user or user `email` (admin only).
        """
        if email:
            return self.get_request('/api2/accounts/%s/' % email).json()
        return self.get_request('/api2/account/info/').json()

    def group_list(self):
        """
        Return list of group info dicts (name, owner, admins, id...)
        """
        return self.get_request('/api2/groups/').json()

    def group_find(self, groupname):
        """
        Find the group named `groupname` (or with ID `groupname`).
        """
        gl = self.group_list()
        logging.debug(gl)
        for group in gl['groups']:
            if group['id'] == groupname or group['name'] == groupname:
                logging.info('Group %s found: %s' % (groupname, group))
                return group
        logging.warn('Group %s not found!' % groupname)
        return None

    def group_add_member(self, group_id, email):
        """
        Add existing member with email `email` to group `group_id` (int).
        Return: member info dict
        """
        try:
            group_id = int(group_id)
        except ValueError:
            group = self.group_find(group_id)
            if group:
                group_id = int(group['id'])
        try:
            r = self.post_request(
                path='/api/v2.1/groups/%d/members/' % group_id,
                params={'email': email}).json()
            return r
        except requests.exceptions.HTTPError as e:
            logging.error(e)
            logging.info('%s probably is already a member of group %s' % (email, group_id))  # TODO: check
        return None

    def group_set_admin(self, group_id, email):
        """
        Set member with email `email` as admin of group `group_id` (int).
        Return: member info dict
        """
        return self.put_request(
            '/api/v2.1/groups/%d/members/%s/' % (group_id, email)).json()

    def group_delete_member(self, group_id, email):
        """
        Delete member with email `email` from group `group_id` (int).
        Return: {'success': True}
        """
        return self.delete_request(
            '/api/v2.1/groups/%d/members/%s/' % (group_id, email)).json()

    def library_list(self, typ=None):
        """
        List current user’s libraries.
        typ (str): mine, shared, group, org (if empty, then all)
        Return: list of library dicts
        """
        path = '/api2/repos/'
        if typ:
            path += '?type=' + typ
        return self.get_request(path).json()

    def library_info(self, lib_id):
        """
        Get information for library with id (hash) `lib_id`
        Return: dict like
        {
            "encrypted": false,
            "password_need": null,
            "mtime": null,
            "owner": "self",
            "id": "632ab8a8-ecf9-4435-93bf-f495d5bfe975",
            "size": 1356155,
            "name": "org",
            "root": "b5227040de360dd22c5717f9563628fe5510cbce",
            "desc": "org file",
            "type": "repo"
        }
        """
        return self.get_request('/api2/repos/%s/' % lib_id)

    def library_get_default(self):
        """
        Return the user’s default library
        """
        # logging.info('Looking for default library')
        return self.get_request('/api2/default-repo/').json()

    def library_create(self, name, description='', password=''):
        """
        Create a new library "name". Password is for encryption.
        """
        data = {
            'name': name,
            'desc': description,
            'passwd': password
            }
        return self.post_request('/api2/repos/', params=data).json()

    def library_delete(self, lib_id):
        """
        Delete library with ID `lib_id`.
        """
        return self.delete_request('/api2/repos/%s/' % lib_id).json()

    def library_rename(self, lib_id, name):
        """
        Rename library with ID `lib_id` into `name`.
        """
        return self.post_request(
            '/api2/repos/%s/?op=rename' % lib_id,
            params={'repo_name': name}).json()

    def library_share(self, lib_id, share_type='group', share_to=None):
        """
        Share a library with a group or user.
        `share_type` may be 'group' or 'user'.
        `share_to` is a group ID (int) or username (email)
        """
        params = {
            'p': '/',
            'permission': 'rw',
            'share_type': share_type
            }
        if share_type == 'group':
            params['group_id'] = int(share_to)
        if share_type == 'user':
            params['username'] = share_to
        return self.put_request('/api2/repos/%s/dir/shared_items/' % lib_id, params)

    def file_find(self, lib_id='all', query='', typ='all', extension='', permissions=False):
        """
        Search for files in library `lib_id` or 'all',
        containing `query` (in name or content),
        with `typ` Text, Document, Image, Video, Audio, PDF, Markdown
        (one of those or 'all') or with `extension`.
        Also return `permissions`?
        """
        valid_types = ('Text', 'Document', 'Image', 'Video', 'Audio', 'PDF', 'Markdown')
        data = {
            'q': query,
            'search_repo': lib_id,
            'with_permission': permissions
            }
        data['search_ftypes'] = 'all'
        if typ != 'all':
            data['search_ftypes'] = 'custom'
            if type in valid_types:
                data['ftype'] = typ
            if extension:
                data['input_fexts'] = extension
        return self.get_request('/api2/search/', params=data).json()

    def file_download(self, lib_id, filename):
        """
        Generate download link for `filename` of `lib_id`
        """
        return self.get_request('/api2/repos/%s/file/?p=%s' % (lib_id, filename)).json()

    def file_move(self, lib_id, filename, targetdir='/', targetlib=None):
        """
        Move the file `filename` (actually path) from library `lib_id`
        into directory `targetdir` of library `targetlib` (defaults to same).
        """
        if not targetlib:
            targetlib = lib_id
        params = {
            'operation': 'move',
            'p': filename,
            'dst_repo': targetlib,
            'dst_dir': targetdir
            }
        return self.post_request('/api2/repos/%s/file/' % lib_id, params=params).json()

    def file_delete(self, lib_id, filename):
        """
        Delete file `filename` (path) from library `lib_id`.
        """
        return self.delete_request('/api2/repos/%s/file/?p=%s' % (lib_id, filename)).json()

    def file_upload(self, lib_id, filepath, target_dir='/', target_filename=''):
        """
        Upload the file at local `filepath` as `target_filename`
        (or original name) into `target_dir` of library `lib_id`.
        Return file info dict
        """
        if not target_filename:
            target_filename = os.path.basename(filepath)
        if not os.path.isfile(filepath):
            logging.error('File not found: %s' % filepath)
            return False
        logging.info('Uploading "%s" to library "%s" as "%s"' % (filepath, lib_id, target_filename))
        # get upload link
        # TODO: check first if file exists, then update
        # https://cloud.seafile.com/api2/repos/{repo-id}/update-link/?p=/update-dir
        # https://cloud.seafile.com/api2/repos/{repo-id}/upload-link/?p=/upload-dir
        g = self.get_request('/api2/repos/%s/upload-link/?p=%s' % (lib_id, target_dir))
        # post file data
        data = {
            'parent_dir': target_dir,
            'ret-json': 1
            }
        r = requests.post(
            g.json(),
            data=data,
            files={'file': open(filepath, 'rb')},
            headers=self.headers)
        logging.info('POST %d %s %s' % (r.status_code, r.url, r.headers))
        r.raise_for_status()
        return r

    def file_info(self, lib_id, filepath):
        """
        Get information on a file. Returns a dict like
        {
            "id": "013d3d38fed38b3e8e26b21bb3463eab6831194f",
            "mtime": 1398148877,
            "type": "file",
            "name": "foo.py",
            "size": 22
        }
        """
        return self.get_request('/api2/repos/%s/file/detail/?p=%s' % (
            lib_id, filepath), params).json()

    def dir_list(self, lib_id, root='/'):
        """
        List the contents (files & dirs) of `root` of library `lib_id`.
        """
        params = {
            'p': root
            }
        return self.get_request('/api2/repos/%s/dir/' % lib_id, params).json()

    def dir_tree(self, lib_id, root='/'):
        """
        Return the whole directory tree (without files)
        as list of dict (no recursion)
        """
        params = {
            'p': root,
            't': 'd',
            'recursive': True
            }
        return self.get_request('/api2/repos/%s/dir/' % lib_id, params).json()

    def dir_create(self, lib_id, dirname, root='/'):
        """
        Create a directory `dirname` below `root` of library `lib_id`
        """
        logging.info('Creating new directory "%s" in Library %s' % (root+dirname, lib_id))
        data = {
            # 'p': root + dirname,
            'operation': 'mkdir'
            }
        return self.post_request('/api2/repos/%s/dir/?p=%s' % (lib_id, root+dirname), params=data)

    def dir_delete(self, lib_id, dirname):
        """
        Delete a directory `dirname` of library `lib_id`
        """
        return self.delete_request('/api2/repos/%s/%s/' % (lib_id, dirname))

    def accounts_list(self):
        """
        (Admin only) List user accounts
        """
        params = {
            'start': -1,
            'limit': -1
            }
        return self.get_request('/api2/accounts/', params).json()

    def account_create(self, email, password, name='', staff=False, groups=()):
        """
        Create new user account (admin only)
        and add to groups
        """
        params = {
            'password': password,
            'is_staff': staff,
            'is_active': True
            }
        logging.debug(params)
        res = self.put_request('/api2/accounts/%s/' % email, params=params).json()
        logging.debug(res)
        if name:
            logging.debug(self.account_update(email, name=name))
        if groups:
            for groupname in groups:
                g = self.group_find(groupname)
                logging.debug('Group %s: %s' % (groupname, g))
                logging.debug(self.group_add_member(g['id'], email))
        return self.account_info(email)

    def account_update(self, email, **kwargs):
        """
        password
        is_staff
        is_active
        name
        note
        storage, the unit is MB.
        """
        params = {}
        for key in ('password', 'is_staff', 'is_active', 'name', 'note', 'storage'):
            if key in kwargs:
                params[key] = kwargs[key]
        return self.put_request('/api2/accounts/%s/' % email, params).json()

    def account_migrate(self, email, to_email):
        """
        Migrate account to existing user `to_email`. (Admin only)
        """
        params = {
            'op': 'migrate',
            'to_user': to_email
            }
        return self.post_request('/api2/accounts/%s/' % email, params).json()

    def account_delete(self, email):
        """
        Delete account of user `email`. (Admin only)
        """
        return self.delete_request('/api2/accounts/%s/' % email)


### DELETE ###

def new_customer(**kwargs):
    """
    kwargs:
    email, password, name, custno, institution (opt)
    """
    c = Connection(
        server='https://seafile.goadress.com',
        username='hraban@fiee.net',
        password='V15ueLL3'
        )
    # add user
    if 'institution' not in kwargs:
        kwargs['institution'] = ''
    logging.debug(kwargs)
    logging.debug('Connection open=%s, headers=%s' % (c.open, c.headers))
    logging.info('ACCOUNT Admin: %s' % c.account_info())
    is_new = False
    try:
        logging.info('ACCOUNT Cust: %s' % c.account_info(kwargs['email']))
    except requests.exceptions.HTTPError:
        is_new = True
        logging.info('Customer %s doesn’t exist yet.' % kwargs['email'])
    if is_new:
        logging.info(c.account_create(kwargs['email'], kwargs['password'], groups=('Kunden',)))
        logging.info('Customer %s was created.' % kwargs['email'])
    else:
        logging.info(c.group_add_member('Kunden', kwargs['email']))
    logging.info(c.account_update(
        kwargs['email'],
        name=kwargs['name'],
        password=kwargs['password'],
        storage=1000,
        note='KdNr.'+kwargs['custno']))
    # customer connection (for non-admin tasks)
    cuc = Connection(
        server='https://seafile.goadress.com',
        username=kwargs['email'],
        password=kwargs['password']
        )

    # Library für Admin anlegen und für Kunden freigeben!

    # Suche, ob es die Lib schon gibt (Namen sind nicht eindeutig)
    liblist = c.library_list('mine')
    libname = 'GoAdress_%s' % kwargs['custno']
    lib_id = None
    for lib in liblist:
        if lib['name'] == libname:
            lib_id = lib['id']
            logging.info('Benutzerbibiothek gefunden: %s' % lib_id)
            break
    if not lib_id:
        userlib = c.library_create(libname, 'GoAdress-Post')
        lib_id = userlib['repo_id']
        logging.info('Neue Benutzerbibiothek: %s' % userlib)
    # create folders
    logging.info('Erzeuge Verzeichnisse in Benutzerbibliothek')
    logging.info(c.dir_create(lib_id, 'Postausgang'))
    # logging.info(c.dir_create(lib_id, 'vernichten'))
    # logging.info(c.dir_create(lib_id, 'archivieren'))
    # logging.info(c.dir_create(lib_id, 'Rechnungen'))
    # share library with Staff
    logging.info(c.library_share(lib_id, share_type='user', share_to=kwargs['email']))
    # upload test data
    for filenr in range(1, 5):
        filepath = '/Users/hraban/workspace/goadress/data/IMG_20180212_%04d.pdf' % filenr
        # logging.info('Uploading %s' % filepath)
        logging.info(c.file_upload(lib_id, filepath))


if __name__ == '__main__':
    c = Connection(
        #server = 'https://sedna.fiee.net',
        #username = 'seafile@fiee.net',
        #password = 'Admin_SeaS1te14!'
        server='https://seafile.goadress.com',
        username='admin@goadress.com',
        password='FkJ296Rd'
    )
    c.connect()
    logging.info(c.account_info())
    new_customer(
        email='geschwurbel@fiee.net',
        name='G. Schwurbel',
        custno='0001',
        password='GggSchwurbel@1!'
        )

