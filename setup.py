#!/usr/bin/env python3
#
# Copyright (c) 2018 by Sylvain Thénault sylvain@lowatt.fr
#
# This program is part of pdfss.
#
# pdfss is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pdfss is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pdfss.  If not, see <https://www.gnu.org/licenses/>.

from setuptools import setup

setup(
    name='pdfss',
    version='1.0.1',
    url='https://github.com/lowatt/lowatt_pdfss',

    license='GPL3',
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: GNU General Public License v3 or later "
        "(GPLv3+)",
        "Operating System :: OS Independent",
    ],
    description='PDF scraping system',
    long_description='Library providing generic and composable helpers to '
    'extract information from pdf/text files',
    author='Sylvain Thénault',
    author_email='info@lowatt.fr',

    py_modules=['pdfss'],
    install_requires=[
        'chardet',  # XXX https://github.com/pdfminer/pdfminer.six/issues/213
        'pdfminer.six',
    ],
)
