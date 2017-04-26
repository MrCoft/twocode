# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import twocode

setup(
    name="Twocode",
    version=twocode.__version__,
    packages=find_packages(),

    entry_points={
        "console_scripts": [
            "twocode = twocode.Twocode:main",
        ],
    },
    install_requires=[
        
    ],

    author="Ondřej Műller",
    author_email="devcoft@gmail.com",
    description="A language designed for translation, featuring intertwined compile-time and runtime execution",
    license="GPLv2",
    url="http://github.com/MrCoft/twocode",
)
