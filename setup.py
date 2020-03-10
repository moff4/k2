#!/usr/bin/env python3
import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='k2',
    version='1.3.2',
    author='Komissarov Andrey',
    author_email='Komissar.off.andrey@mail.ru',
    description='Framework for simple services',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/moff4/k2',
    install_requires=[
        'pygost',
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
