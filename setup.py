from setuptools import setup, find_packages


setup(
    name='zeit.connector',
    version='2.10.1.dev0',
    author='Tomas Zerolo, gocept, Zeit Online',
    author_email='zon-backend@zeit.de',
    url='http://www.zeit.de/',
    description="DAV interface",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='BSD',
    namespace_packages=['zeit'],
    install_requires=[
        'ZConfig',
        'ZODB',
        'gocept.cache>=0.2.2',
        'gocept.lxml',
        'lxml',
        'setuptools',
        'zc.set',
        'zope.app.file',
        'zope.cachedescriptors',
        'zope.event',
        'zope.interface',
        'zope.schema',
    ],
    extras_require={
        'zope': [
            'BTrees',
            'gocept.runner>=0.2',
            'persistent',
            'transaction',
            'zope.app.appsetup',
            'zope.app.component>=3.4b3',
            'zope.authentication',
            'zope.cachedescriptors',
            'zope.component',
            'zope.file',
            'zope.location>=3.4b2',
            'zope.security',
            'zope.testing',
        ],
        'test': [
            'mock',
            'zc.queue',
            'zope.annotation',
            'zope.app.zcmlfiles',
            'zope.app.testing',
        ],
    },
    entry_points={'console_scripts': [
        'refresh-cache = zeit.connector.invalidator:invalidate_whole_cache',
        'set-properties = zeit.connector.restore:set_props_from_file',
    ]}
)
