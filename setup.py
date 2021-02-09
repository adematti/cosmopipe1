import os
import sys
from setuptools import setup

setup_keywords = dict()
setup_keywords['name'] = 'cosmopipe'
setup_keywords['description'] = 'Cosmological pipeline'
setup_keywords['author'] = 'Arnaud de Mattia'
setup_keywords['author_email'] = ''
setup_keywords['license'] = 'GPL3'
setup_keywords['url'] = 'https://github.com/adematti/cosmopipe'
sys.path.insert(0,os.path.abspath('cosmopipe/'))
import version
setup_keywords['version'] = version.__version__
setup_keywords['install_requires'] = []
setup_keywords['packages'] = ['cosmopipe']
setup_keywords['package_dir'] = {'cosmopipe':'cosmopipe'}

setup_keywords['cmdclass'] = {}

setup(**setup_keywords)
