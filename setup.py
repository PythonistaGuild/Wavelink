# -*- coding: utf-8 -*-

"""MIT License

Copyright (c) 2019 EvieePy(MysterialPy)

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
import re
from setuptools import setup


on_rtd = os.getenv('READTHEDOCS') == 'True'

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

if on_rtd:
    requirements.append('sphinx==1.7.4')
    requirements.append('sphinxcontrib-napoleon')
    requirements.append('sphinxcontrib-asyncio')
    requirements.append('sphinxcontrib-websupport')
    requirements.append('Pygments')

version = '0.2.09'

readme = ''
with open('README.rst') as f:
    readme = f.read()

setup(name='wavelink',
      author='EvieePy',
      url='https://github.com/EvieePy/Wavelink',
      version=version,
      packages=['wavelink'],
      license='MIT',
      description='A versatile LavaLink wrapper for Discord.py',
      long_description=readme,
      include_package_data=True,
      install_requires=requirements,
      classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
      ]
)
