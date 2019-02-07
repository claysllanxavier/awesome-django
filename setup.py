# -*- coding: utf-8 -*-

import os
from setuptools import find_packages, setup

VERSION = "1.0.1.dev"
AUTHOR = "Claysllan Xavier"
AUTHOR_EMAIL = 'claysllan@gmail.com'

LONG_DESCRIPTION = """
Projeto padrão para os meus projetos que serão desenvolvidos com o Django.

Conta com o build e a dashboard completa.

Github: https://github.com/claysllanxavier/awesome-django/blob/master/README.md

"""
# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-smart',
    version=VERSION,
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='It is a Django app to generate forms, templates, Api Rest and views for apps of your project.',
    long_description=LONG_DESCRIPTION,
    url='https://github.com/claysllanxavier/awesome-django.git',
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ]
)