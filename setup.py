#!/usr/bin/env python3

import setuptools

setuptools.setup(
      name='csv2owl',
      version='1.0',
      description='A tool to generate owl vocabularies for csv properties and classes files',
      author='Hugo Delahousse',
      author_email='hugo.delahousse@gmail.com',
      url='https://www.github.com/hugodelahousse/owl2csv/',
      license='MIT',
      scripts=['csv2owl'],
      install_requires=[
            'click',
            'rdflib',
            'rdflib-jsonld',
      ]
)
