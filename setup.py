try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'nhlpyscrape',
    'author': 'Peter Von der Porten',
    'url': 'https://github.com/p-vdp/nhlpyscrape/',
    'download_url': 'https://github.com/p-vdp/nhlpyscrape/releases',
    'author_email': 'pvonderporten@gmail.com',
    'version': '0.1',
    'install_requires': ['matplotlib', 'pytz', 'requests', 'scipy'],
    'packages': ['nhlpyscrape'],
    'scripts': [],
    'name': 'nhlpyscrape'
}

setup(**config)
