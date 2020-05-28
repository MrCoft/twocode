# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import find_packages
import twocode

with open('README.md', encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='Twocode',
    version=twocode.__version__,
    description='Language designed for code generation. Solve difficult problems by adding new language features from within your code.',
    long_description=long_description,
    author='Ondřej Műller',
    author_email='devcoft@gmail.com',
    url='https://github.com/MrCoft/twocode',
    download_url=twocode.url,
    license='MIT',

    packages=find_packages(exclude=['tests']),
    install_requires=[],
    include_package_data=True,
    zip_safe=False,
    test_suite='tests',
    # cmdclass={'test': PyTest},
    extras_require={
        'testing': ['pytest', 'pytest-xdist'],
    },
    entry_points={
        'console_scripts': [
            'twocode = twocode:main',
        ],
    },

    classifiers=[
        'Programming Language :: Other',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Framework :: Jupyter',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Software Development :: Code Generators',
    ],
)
