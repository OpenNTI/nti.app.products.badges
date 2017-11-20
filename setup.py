import codecs
from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
        "nti_badge_sync_db = nti.app.products.badges.utils.sync:main",
    ],
    "z3c.autoinclude.plugin": [
        'target = nti.app.products',
    ],
}

TESTS_REQUIRE = [
    'fudge',
    'nti.app.testing',
    'nti.testing',
    'simplejson',
    'zope.dottedname',
    'zope.testrunner',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.app.products.badges',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI Badges Product Integration",
    long_description=(
        _read('README.rst')
        + '\n\n'
        + _read("CHANGES.rst")
    ), license='Apache',
    keywords='pyramid badges',
    classifiers=[
        'Framework :: Zope',
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    url="https://github.com/NextThought/nti.app.products.badges",
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti', 'nti.app', 'nti.app.products'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'alembic',
        'nti.app.client_preferences',
        'nti.badges',
        'nti.common',
        'nti.contentfragments',
        'nti.externalization',
        'nti.links',
        'nti.property',
        'nti.tahrir_api',
        'nti.traversal',
        'pyramid',
        'requests',
        'six',
        'sqlalchemy',
        'z3c.pagelet',
        'z3c.template',
        'zope.cachedescriptors',
        'zope.component',
        'zope.container',
        'zope.event',
        'zope.generations',
        'zope.interface',
        'zope.i18nmessageid',
        'zope.lifecycleevent',
        'zope.location',
        'zope.preference',
        'zope.security',
        'zope.traversing',
        'zope.viewlet',
    ],
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
    entry_points=entry_points,
)
