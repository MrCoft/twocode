from .testdefs import *

name_tests(
    # syntax,
    syntax = cmp("class A: {}"),
    anon = cmp("class: {}"),
    # fails - class A {}
    # stmt
    stmt = cmp("var A = class: {}"),

    repr_var = evals("class: var x"),
    repr_var_value = evals("class: var x = 2"),
)







# not printing this
# long printed correctly




# can't parse <stmt>at: 'var' WS 'type'

"""
type Token:
    var type:String
    var data:String
    func __init__(?type:String, ?data:String):
        this.type = type
        if data:
            this.data = data
    func __repr__():
        return type + (if data "({})".format(repr(data)) else "")
"""







# null.__type__ = Null
# Null().__type__ = Null

# Dynamic works?!

# getter property
# [ ] static, getters


# type not evaluating
# the thing where in some places typing doesnt work - func args or smth


"""
a func that returns a type object
Func<a,b> reads as a->b
<> is just syntax to create an internal field __params__
    a weird scope visible for types of the class
    original - compatible, have to be types
func has none and is on request
"""

# scope, getattr, the impl comment

# class getattr
# smells like internals -> getter

# classes now store the frame
# see local names in a module during initialization