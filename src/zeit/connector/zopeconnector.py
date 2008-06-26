# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt
# $Id$
"""Connector which integrates into Zope CA."""

import logging
import os
import threading

import transaction
import transaction.interfaces

import zope.component
import zope.event
import zope.interface

import zope.app.appsetup.product

import gocept.cache.property

import zeit.connector.connector
import zeit.connector.interfaces


logger = logging.getLogger(__name__)


class ZopeConnector(zeit.connector.connector.Connector):

    def create_connection(self, root):
        connection = super(self.__class__, self).create_connection(root)
        dm = connection._connector_datamanager = DataManager(self)
        transaction.get().join(dm)
        return connection

    def get_datamanager(self):
        conn = self.get_connection()
        return conn._connector_datamanager

    def lock(self, id, principal, until):
        locktoken = super(self.__class__, self).lock(id, principal, until)
        datamanager = self.get_datamanager()
        datamanager.add_cleanup(self.unlock, id, locktoken)
        return locktoken

    def unlock(self, id, locktoken=None):
        locktoken = super(self.__class__, self).unlock(id, locktoken)
        self.get_datamanager().remove_cleanup(self.unlock, id, locktoken)
        return locktoken

    @property
    def body_cache(self):
        return zope.component.getUtility(
            zeit.connector.interfaces.IResourceCache)

    @property
    def property_cache(self):
        return zope.component.getUtility(
            zeit.connector.interfaces.IPropertyCache)

    @property
    def child_name_cache(self):
        return zope.component.getUtility(
            zeit.connector.interfaces.IChildNameCache)

    @property
    def locktokens(self):
        return zope.component.getUtility(
            zeit.connector.interfaces.ILockInfoStorage)

    def _invalidate_cache(self, id, parent=False):
        """invalidate cache."""
        invalidate = [id]
        if parent:
            parent, last = self._id_splitlast(id)
            invalidate.append(parent)

        for id in invalidate:
            logger.debug("Invalidating %s" % id)
            zope.event.notify(
                zeit.connector.interfaces.ResourceInvaliatedEvent(id))


def connectorFactory():
    """Factory for creating the connector with data from zope.conf."""
    config = zope.app.appsetup.product.getProductConfiguration(
        'zeit.connector')
    if config:
        root = config.get('document-store')
        if not root:
            raise ZConfig.ConfigurationError(
                "WebDAV server not configured properly.")
        search_root = config.get('document-store-search')
    else:
        root = os.environ.get('connector-url')
        search_root = os.environ.get('search-connector-url')

    if not root:
        raise ZConfig.ConfigurationError(
            "zope.conf has no product config for zeit.connector.")

    return ZopeConnector(dict(
        default=root,
        search=search_root))


class DataManager(object):
    """Takes care of the transaction process in Zope. """

    zope.interface.implements(transaction.interfaces.IDataManager)

    def __init__(self, connector):
        self.connector = connector
        self.cleanup = []

    def abort(self, trans):
        self._cleanup()
        self.connector.disconnect()

    def tpc_begin(self, trans):
        pass

    def commit(self, trans):
        pass

    def tpc_vote(self, trans):
        pass

    def tpc_finish(self, trans):
        self.connector.disconnect()

    def tpc_abort(self, trans):
        self._cleanup()
        self.connector.disconnect()

    def sortKey(self):
        return str(id(self))

    def savepoint(self):
        # This would be a point to flush pending commands.
        return ConnectorSavepoint()

    def add_cleanup(self, method, *args, **kwargs):
        self.cleanup.append((method, args, kwargs))

    def remove_cleanup(self, method, *args, **kwargs):
        try:
            self.cleanup.remove((method, args, kwargs))
        except ValueError:
            pass

    def _cleanup(self):
        for method, args, kwargs in self.cleanup:
            method(*args, **kwargs)
        self.cleanup[:] = []


class ConnectorSavepoint(object):

    zope.interface.implements(transaction.interfaces.IDataManagerSavepoint)

    def rollback(self):
        raise Exception("Can't roll back connector savepoints.")


