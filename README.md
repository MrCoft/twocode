# Twocode
[![TravisCI Build Status](https://api.travis-ci.org/MrCoft/twocode.svg?branch=master)](https://travis-ci.org/MrCoft/twocode) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

A language designed for code generation. Load code in an interpreter, edit and create classes and functions, then transpile it to the target language.

### Demo
Check out [this Jupyter Notebook](notebooks/codeedit.ipynb) demonstrating code editing in Twocode!

### Prerequisites
* Python 3

### Installation
```bash
easy_install https://github.com/MrCoft/twocode/tarball/master
twocode
```
Starts the Twocode console.

### Status
Missing key features such as typing, advanced class fields, transpiler, native implementation.

### Why code generation?
Conventional code has a mostly 1-to-1 correspondence between source code and runtime instructions.\
All language features abstract over this, but unless they are programmable, they are limited.\
**_Sometimes the most readable code isn't fast and the fast code isn't readable._**\
Such problems are best modelled by setting up configuration objects, then building code from them.

Examples of problems solved using code generation:

* lexers, parsers
* GPU shaders
* symbolic math
* dataflow graphs
* script assets

### tl;dr
`think Lisp, write Python, compile Java`
