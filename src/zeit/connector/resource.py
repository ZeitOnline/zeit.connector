import persistent.mapping
import zeit.connector.interfaces
import zope.interface


class WebDAVProperties(persistent.mapping.PersistentMapping):

    zope.interface.implements(zeit.connector.interfaces.IWebDAVProperties)

    def __repr__(self):
        return object.__repr__(self)


class ReadOnlyWebDAVProperties(WebDAVProperties):

    def __init__(self, adict=None):
        super(ReadOnlyWebDAVProperties, self).__init__()
        if adict is not None:
            super(ReadOnlyWebDAVProperties, self).update(adict)

    def __delitem__(self, *args, **kwargs):
        raise RuntimeError("Cannot write on ReadOnlyWebDAVProperties")

    def __setitem__(self, *args, **kwargs):
        raise RuntimeError("Cannot write on ReadOnlyWebDAVProperties")

    def clear(self, *args, **kwargs):
        raise RuntimeError("Cannot write on ReadOnlyWebDAVProperties")

    def update(self, *args, **kwargs):
        raise RuntimeError("Cannot write on ReadOnlyWebDAVProperties")

    def setdefault(self, *args, **kwargs):
        raise RuntimeError("Cannot write on ReadOnlyWebDAVProperties")

    def pop(self, *args, **kwargs):
        raise RuntimeError("Cannot write on ReadOnlyWebDAVProperties")

    def popitem(self, *args, **kwargs):
        raise RuntimeError("Cannot write on ReadOnlyWebDAVProperties")


class Resource(object):
    """Represents a resource in the webdav."""

    zope.interface.implements(zeit.connector.interfaces.IResource)

    def __init__(self, id, name, type, data, properties=None, contentType=''):
        self.id = id
        self.__name__ = name
        self.type = type
        self.data = data
        if properties is None:
            properties = {}
        self.properties = WebDAVProperties(properties)
        self.contentType = contentType


class CachedResource(object):
    """Represents a resource in the webdav."""

    zope.interface.implements(zeit.connector.interfaces.IResource)

    def __init__(self, id, name, type_name, property_getter, body_getter,
                 content_type):
        self.id = id
        self.__name__ = name
        self.type = type_name
        self._property_getter = property_getter
        self._body_getter = body_getter
        self.contentType = content_type

    @property
    def data(self):
        return self._body_getter()

    @property
    def properties(self):
        return ReadOnlyWebDAVProperties(self._property_getter())


class WriteableCachedResource(CachedResource):
    """Used by mock connector"""

    def __init__(self, id, name, type_name, property_getter, body_getter,
                 content_type):
        super(WriteableCachedResource, self).__init__(
            id, name, type_name, property_getter, body_getter, content_type)
        self._properties = WebDAVProperties(self._property_getter())

    @property
    def properties(self):
        return self._properties
