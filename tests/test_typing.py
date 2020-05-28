"""
this will be messy


class A: {}
class B(A): {}
var a:A = B() // okay
var b:B = A() // ConversionError  TypeError
 not internal error though, dunno




for a in b:
    b is typed, a is its reftype

with a as b:
    b is a's reftype

from module import *
    same var types

import module (that is a module subtype)
    it is its reftype

that reftype works at all?


"""