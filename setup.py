#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from ddcsequences import infos


setup(name='ddcsequences',
      version=infos.__version__,
      description='Framework to test DDC sequences with BAC0',
      author=infos.__author__,
      author_email=infos.__email__,
      url=infos.__url__,
      download_url = infos.__download_url__,
      keywords = ['bacnet', 'building', 'automation', 'test'],
      packages=[
          'ddcsequences',
          'ddcsequences.vendors',
          'ddcsequences.vendors.jci',
          ],
      install_requires=[
          'BAC0',
#          'bokeh',
          ],
      long_description=open('README.rst').read(),
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: Utilities",
          ],)