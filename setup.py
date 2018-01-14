# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import twocode

setup(
    name = "Twocode",
    version = twocode.__version__,
    packages = find_packages(exclude="tests".split()) + ["twocode.code"],
    # REASON: without, it installs an accessible "tests" module
    package_dir = {"twocode.code": "code"},
    package_data = {"twocode.code": "*"},
    # REASON:
    # Manifest.in doesn't work
    # I can't add "code" as a package because it doesn't have __init__.py
    # it has to be hidden, this works, twocode.code just needs to exist

    entry_points = {
        "console_scripts": [
            "twocode = twocode.Twocode:main",
        ],
    },
    install_requires = [],
    include_package_data = True,
    test_suite = "tests",
    tests_require = ["pytest", "pytest-runner"],
    extras_require = {
        "testing": ["pytest"],
    },

    author = "Ondřej Műller",
    author_email = "devcoft@gmail.com",
    description = "A language designed for code generation. Load a codebase in an interpreter, edit and create classes and functions, then translate it into the target language.",
    license = "MIT",
    url = "http://github.com/MrCoft/twocode",
)