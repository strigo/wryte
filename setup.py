import os
import codecs
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open
    return codecs.open(os.path.join(here, *parts), 'r').read()


setup(
    name='wryte',
    version="1.0.0",
    url='https://github.com/strigo/wryte',
    author='strigo.io',
    author_email='ops@strigo.io',
    license='LICENSE',
    platforms='All',
    description='Simply Log',
    long_description=read('README.rst'),
    py_modules=['wryte'],
    entry_points={'console_scripts': ['wryte = wryte:main']},
    extras_require={
        'color': ['colorama'],
        'cli': ['click>=6.7'],
    },
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
