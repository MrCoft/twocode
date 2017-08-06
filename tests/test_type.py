from twocode.Tests import *

tests_class = name_tests(
    # syntax,
    syntax=cmp("type A: {}"),
    anon=cmp("type: {}"),
    # fails - type A {}
    # stmt
    stmt=cmp("var A = type: {}"),

    repr_var=evals("type: var x"),
    repr_var_value=evals("type: var x = 2"),
)




















# null.__type__ = Null
# Null().__type__ = Null

# Dynamic works?!