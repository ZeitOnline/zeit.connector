# Copyright (c) 2007-2008 gocept gmbh & co. kg
# See also LICENSE.txt
# $Id$
"""Connect to the CMS backend."""

import StringIO
import datetime
import os
import os.path
import urlparse

import lxml.etree
import gocept.lxml.objectify

import persistent.mapping

import zope.interface

import zope.app.file.image

import zeit.connector.interfaces
import zeit.connector.resource

ID_NAMESPACE = u'http://xml.zeit.de/'

repository_path = os.path.join(os.path.dirname(__file__), 'testcontent')


class Connector(object):
    """Connect to the CMS backend.

    The current implementation does *not* talk to the CMS backend but to
    some directory containing test content.

    """

    zope.interface.implements(zeit.connector.interfaces.IConnector)

    def __init__(self):
        self._reset()

    def _reset(self):
        self._locked = {}
        self._data = {}
        self._paths = {}
        self._deleted = set()
        self._properties = {}

    def listCollection(self, id):
        """List the filenames of a collection identified by path. """
        path = self._path(id)
        absolute_path = self._absolute_path(path)
        names = set()
        if os.path.isdir(absolute_path):
            names = names | set(os.listdir(self._absolute_path(path)))
        names = names | self._paths.get(path, set())
        for name in sorted(names):
            name = unicode(name)
            if name.startswith('.'):
                continue
            id = self._make_id(path + (name, ))
            if id in self._deleted:
                continue
            yield (name, id)

    def getResourceType(self, id):
        __traceback_info__ = id
        path = self._absolute_path(self._path(id))
        if id in self._deleted:
            raise KeyError("The resource %r does not exist." % id)
        if os.path.isdir(path):
            return 'collection'
        data = self._get_file(id).read(200)
        if '<article>' in data:
            # Ok, this is hardcore. But it's not production code, is it.
            return 'article'
        if '<channel>' in data:
            return 'channel'
        if '<centerpage>' in data:
            return 'centerpage'
        if '<testtype>' in data:
            return 'testcontenttype'
        content_type, width, height = zope.app.file.image.getImageInfo(data)
        if content_type:
            return 'image'
        return 'unknown'

    def __getitem__(self, id):
        if id in self._deleted:
            raise KeyError(id)
        properties = self._get_properties(id)
        type = properties.get(
            zeit.connector.interfaces.RESOURCE_TYPE_PROPERTY)
        if type is None:
            type = self.getResourceType(id)
            properties[
                zeit.connector.interfaces.RESOURCE_TYPE_PROPERTY] = type
        if type == 'collection':
            data = StringIO.StringIO()
        else:
            data = self._get_file(id)
        return zeit.connector.resource.Resource(
            id, self._path(id)[-1], type, data, properties)

    def __setitem__(self, id, object):
        if id in self._deleted:
            self._deleted.remove(id)
        resource = zeit.connector.interfaces.IResource(object)
        # Just a very basic in-memory data storage for testing purposes.
        resource.data.seek(0)
        self._data[id] = resource.data.read()
        path = self._path(id)[:-1]
        name = self._path(id)[-1]
        self._paths.setdefault(path, set()).add(name)
        resource.properties[
            zeit.connector.interfaces.RESOURCE_TYPE_PROPERTY] = resource.type
        self._set_properties(id, resource.properties)

    def __delitem__(self, id):
        resource = self[id]
        for name, uid in self.listCollection(id):
            del self[uid]
        self._deleted.add(id)
        self._data.pop(id, None)

    def __contains__(self, id):
        try:
            resource = self[id]
        except KeyError:
            return False
        return True

    def add(self, object):
        resource = zeit.connector.interfaces.IResource(object)
        self[resource.id] = resource

    def copy(self, old_id, new_id):
        self[new_id] = self[old_id]
        if not new_id.endswith('/'):
            new_id = new_id + '/'
        for name, uid in self.listCollection(old_id):
            self.copy(uid, urlparse.urljoin(new_id, name))


    def move(self, old_id, new_id):
        if new_id in self:
            raise zeit.connector.interfaces.MoveError(
                old_id,
                "Could not move %s to %s, because target alread exists." % (
                    old_id, new_id))

        self.copy(old_id, new_id)
        del self[old_id]

    def changeProperties(self, id, properties):
        self._set_properties(id, properties)

    def lock(self, id, principal, until):
        """Lock resource for principal until a given datetime."""
        #locked_by, locked_until = self.locked(id)
        #if locked_by is not None and locked_by != principal:
        #    raise zeit.cms.interfaces.LockingError(
        #        "%s is already locked." % id)
        self._locked[id] = (principal, until, True)

    def unlock(self, id, locktoken=None):
        del self._locked[id]
        return locktoken

    def locked(self, id):
        return self._locked.get(id, (None, None, None))

    def search(self, attributes, expression):
        print  "Searching: ", expression._collect()._render()

        unique_ids = [
            u'http://xml.zeit.de/online/2007/01/Somalia', 
            u'http://xml.zeit.de/online/2007/01/Saarland',
            u'http://xml.zeit.de/2006/52/Stimmts']

        metadata = ('pm', '07') + len(attributes) * (None,)
        metadata = metadata[:len(attributes)]

        return ((unique_id,) + metadata for unique_id in unique_ids)

    # internal helpers

    def _absolute_path(self, path):
        if not path:
            return repository_path
        return os.path.join(repository_path, os.path.join(*path))

    def _path(self, id):
        if not id.startswith(ID_NAMESPACE):
            raise ValueError("The id %r is invalid." % id)
        id = id.replace(ID_NAMESPACE, '', 1)
        if not id:
            return ()
        return tuple(id.split('/'))

    def _get_file(self, id):
        if id in self._data:
            return StringIO.StringIO(self._data[id])
        filename = self._absolute_path(self._path(id))
        __traceback_info__ = (id, filename)
        try:
            return file(filename, 'rb')
        except IOError:
            raise KeyError("The resource %r does not exist." % id)

    def _make_id(self, path):
        return urlparse.urljoin(ID_NAMESPACE, '/'.join(
            element for element in path if element))

    def _get_properties(self, id):
        properties = self._properties.get(id)
        if properties is not None:
            return properties
        # We have not properties for this type, try to read it from the file.
        # This is sort of a hack, but we need it to get properties at all
        if self.getResourceType(id) == 'collection':
            return {}
        data = self._get_file(id)
        properties = {}
        try:
            xml = lxml.etree.parse(data)
        except lxml.etree.LxmlError:
            pass
        else:
            nodes = xml.xpath('//head/attribute')
            for node in nodes:
                properties[node.get('name'), node.get('ns')] = (
                    node.text)
        properties[('getlastmodified', 'DAV:')] = (
            u'Fri, 07 Mar 2008 12:47:16 GMT')
        self._properties[id] = properties
        return properties

    def _set_properties(self, id, properties):
        stored_properties = self._get_properties(id)
        for ((name, namespace), value) in properties.items():
            if name.startswith('get'):
                continue
            stored_properties[(name, namespace)] = value
            if value is zeit.connector.interfaces.DeleteProperty:
                del stored_properties[(name, namespace)]
        self._properties[id] = stored_properties
