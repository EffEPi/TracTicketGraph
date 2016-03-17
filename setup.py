#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracTicketGraph',
    version = '1.0',
    packages = ['ticketgraph'],
    package_data = { 'ticketgraph' : [ 'htdocs/*.*', 'templates/*.*' ] },

    author = 'Fabrizio Parrella',
    author_email = 'fabrizio@bibivu.com',
    description = 'Graphs Trac tickets over time',
    long_description = 'A Trac plugin that displays a visual graph of ticket changes over time, based on Colin Snover version.',
    license = 'MIT',
    keywords = 'trac plugin ticket statistics graph',
    classifiers = [
        'Framework :: Trac',
    ],

    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'ticketgraph = ticketgraph',
        ],
    }
)
