# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import twocode

import os
ROOT = os.path.abspath(os.path.dirname(__file__))
codebase_files = [
    os.path.abspath(os.path.join(root, file))[len(ROOT):].lstrip(os.path.sep)
for root, dirs, files in os.walk(os.path.join(ROOT, "code")) for file in files]
print(codebase_files)
codebase_files = [(os.path.join("twocode", os.path.dirname(file)).replace(os.path.sep, "/"), [file.replace(os.path.sep, "/")]) for file in codebase_files]
print(codebase_files)

setup(
    name = "Twocode",
    version = twocode.__version__,
    packages = find_packages(exclude="tests".split()),
    # REASON: without, it installs an accessible "tests" module
    data_files = codebase_files,
    # REASON:
    # Manifest.in does nothing
    # I can't add "code" as a package because it doesn't have __init__.py
    # it has to be hidden, twocode.code just needs to exist
    # when installing from git, it deletes twocode/code/__init__.py?
    # package_data uses glob whose **/* is recursive 1 level only
    # listed manually because nothing else works

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