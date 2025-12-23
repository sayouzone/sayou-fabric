#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# OpenDart, FnGuide, Naver, Yahoo Finance, SEC EDGAR - data crawler
# https://github.com/sayouzone/sayou-fabric/packages-dev/sayou-stock

"""sayou-stock - market data crawler"""

from setuptools import setup, find_packages
# from codecs import open
import io
from os import path

# --- get version ---
version = "unknown"
with open("sayou-stock/src/sayou/stock/version.py") as f:
    line = f.read().strip()
    version = line.replace("version = ", "").replace('"', '')
# --- /get version ---


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with io.open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sayou-stock',
    version=version,
    description='Crawle market data from OpenDart, FnGuide, Naver Finance, Yahoo! Finance API, SEC EDGAR',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/sayouzone/sayou-fabric/packages-dev/sayou-stock',
    author='Chan Woo Kim',
    author_email='chanwoo@sayouzone.com',
    license='Apache',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',


        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    platforms=['any'],
    keywords='pandas, yahoo finance, pandas datareader',
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'examples']),
    install_requires=['pandas>=1.3.0', 'numpy>=1.16.5',
                      'requests>=2.31', 'multitasking>=0.0.7',
                      'platformdirs>=2.0.0', 'pytz>=2022.5',
                      'frozendict>=2.3.4', 'peewee>=3.16.2',
                      'beautifulsoup4>=4.11.1', 'curl_cffi>=0.7',
                      'protobuf>=3.19.0', 'websockets>=13.0'],
    extras_require={
        'nospam': ['requests_cache>=1.0', 'requests_ratelimiter>=0.3.1'],
        'repair': ['scipy>=1.6.3'],
    },
    # Include protobuf files for websocket support
    package_data={
        'sayou-stock': ['pricing.proto', 'pricing_pb2.py'],
    },
    include_package_data=True,
    # Note: Pandas.read_html() needs html5lib & beautifulsoup4
    entry_points={
        'console_scripts': [
            'sayou-stock=sample:main',
        ],
    },
)

print("""
NOTE: yfinance is not affiliated, endorsed, or vetted by Yahoo, Inc.

You should refer to Yahoo!'s terms of use for details on your rights
to use the actual data downloaded.""")