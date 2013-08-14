from setuptools import setup, find_packages

setup(
    name='zeit.connector',
    version='2.0.1.dev0',
    author='Tomas Zerolo, Christian Zagrodnick',
    author_email='tomas@tuxteam.de, cz@gocept.com',
    url='http://trac.gocept.com/zeit',
    description="""\
""",
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe=False,
    license='gocept proprietary',
    namespace_packages = ['zeit'],
    install_requires=[
        'ZODB3>=3.8b4',
        'gocept.cache>=0.2.2',
        'gocept.lxml',
        'gocept.runner>=0.2',
        'mock',
        'setuptools',
        'unittest2',
        'zc.queue',
        'zc.set',
        'zope.annotation',
        'zope.app.appsetup',
        'zope.app.component>=3.4b3',
        'zope.app.file',
        'zope.app.testing',
        'zope.app.zcmlfiles',
        'zope.authentication',
        'zope.cachedescriptors',
        'zope.component',
        'zope.file',
        'zope.interface',
        'zope.location>=3.4b2',
        'zope.testing',
        ],
    entry_points = """
        [console_scripts]
        refresh-cache = zeit.connector.invalidator:invalidate_whole_cache
        """
)
