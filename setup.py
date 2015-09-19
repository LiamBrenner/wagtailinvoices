#!/usr/bin/env python
"""
Install wagtailinvoices using setuptools
"""

from wagtailinvoices import __version__

with open('README.md', 'r') as f:
    readme = f.read()

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='wagtailinvoices',
    version=__version__,
    description='Invoice mod for the Wagtail CMS',
    long_description=readme,
    author='Liam Brenner',
    author_email='liam.brenner@gmail.com',
    url='https://bitbucket.org/sablewalnut/wagtailinvoices',

    install_requires=[
        'wagtail>=1.0b2',
        'xhtml2pdf==0.0.6',
        'django-uuidfield==0.5.0',
        'braintree>=3.13.0'
    ],
    zip_safe=False,
    license='BSD License',

    packages=find_packages(),

    include_package_data=True,
    package_data={},

    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
    ],
)
