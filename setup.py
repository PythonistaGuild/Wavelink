# -*- coding: utf-8 -*-

"""MIT License

Copyright (c) 2019-2020 PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import pathlib
import re

import setuptools


ROOT = pathlib.Path(__file__).parent
ON_RTD = os.getenv('READTHEDOCS') == 'True'


with open(ROOT / 'requirements.txt', encoding='utf-8') as f:
    REQUIREMENTS = f.readlines()

if ON_RTD:
    REQUIREMENTS.extend((
        'pygments',
        'sphinx==1.7.4',
        'sphinxcontrib-asyncio',
        'sphinxcontrib-napoleon',
        'sphinxcontrib-websupport',
    ))

with open(ROOT / 'README.rst', encoding='utf-8') as f:
    README = f.read()

with open(ROOT / 'wavelink' / '__init__.py', encoding='utf-8') as f:
    VERSION = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)


setuptools.setup(
    name='wavelink',
    author='EvieePy',
    url='https://github.com/EvieePy/Wavelink',
    version=VERSION,
    packages=['wavelink'],
    license='MIT',
    description='A versatile LavaLink wrapper for Discord.py',
    long_description=README,
    include_package_data=True,
    install_requires=REQUIREMENTS,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    python_requires='>=3.7'
)
