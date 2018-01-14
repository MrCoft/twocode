"""
import a
import a.b
import a.B (and is the cross thing)
import a.*
import a.b as c
from a import b, c
import a, b
from _ import *
"""
# objects see their own vars
# function args are seen ((x)->x)(2)

# import bogus
# errors
# bogus -> NameError
"""
del list[index]
del x
del dict[key]

delete object.member, which removes member as a key from object

only related to:
dynamics
dicts
reloading modules
gc or c++ memory management
kind of the opposite of declare tbh
"""
# module.copy()


# in

# a ast wrapper AST Stack CodeStack
# term expr

# tests:
# code imports, CODE does not




# i'd love a reimport func

# INSPECT:
# i should be able to see vars of a thing
# scope_stack[-1]
# inspect

# cancel import if errors?


# import a as b, c as d
                # from a import b
                # import a.*
# error on * *
# allow **? dunno


# cannot declare in object - artificial scope



# test method in class
# test fake module declaration through ins and qualnames
# test closure

# can't set this




# getattr errors from importing
# importing with errors does not set the name