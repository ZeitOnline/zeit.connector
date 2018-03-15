import argparse
import logging
import sys
import zeit.connector.connector
import zeit.connector.filesystem


log = logging.getLogger(__name__)


def put_from_file(argv=None):
    parser = argparse.ArgumentParser(
        description='Update DAV resources from filesystem data')
    parser.add_argument(
        'uniqueId',
        help='uniqueId, prefix either http://xml.zeit.de or /var/cms/work')
    parser.add_argument('--dav-url', help='DAV URL',
                        default='http://cms-backend.zeit.de:9000/cms/work/')
    parser.add_argument('--fs-path', help='Filesystem path',
                        default='/var/cms/work')
    parser.add_argument('--verbose', '-v', help='Increase verbosity',
                        action='store_true')
    options = parser.parse_args(argv)
    setup_logging(logging.INFO if not options.verbose else logging.DEBUG)

    if not options.dav_url.endswith('/'):
        options.dav_url += '/'
    if options.fs_path.endswith('/'):
        options.fs_path = options.fs_path[:-1]
    if options.uniqueId.startswith('/var/cms/work'):
        options.uniqueId = options.uniqueId.replace(
            '/var/cms/work', 'http://xml.zeit.de', 1)

    dav = zeit.connector.connector.Connector({'default': options.dav_url})
    fs = zeit.connector.filesystem.Connector(options.fs_path)
    put(dav, fs, options.uniqueId)


def put(dav, fs, uniqueId):
    log.info('Processing %s', uniqueId)
    res = fs[uniqueId]
    dav[uniqueId] = res
    if res.type == 'collection':
        for child in fs.listCollection(uniqueId):
            put(dav, fs, uniqueId)


def setup_logging(level=logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)-5.5s %(name)s %(message)s'))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)
