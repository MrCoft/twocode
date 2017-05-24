from twocode.Tests import *

tests_class = name_tests(
    # syntax,
    syntax=auto_cmp("class A: {}"),
    anon=auto_cmp("class: {}"),
    # stmt
    stmt=auto_cmp("var A = class: {}"),
)