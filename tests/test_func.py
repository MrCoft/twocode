from twocode.Tests import *

name_tests(
    # syntax
    syntax=cmp("func f(): {}"),
    syntax_args=cmp("func f(a:A=1, b:B=2)->C: {}"),
    # format
    format_enter=cmp("func f():\n\t1\n\t2"),
    format_single=cmp("func f(): 1"),
    format_strip=cmp("func f(): {;0;}", "func f(): 0"),
    format_anon=cmp("func(): {}"),
    # stmt
    stmt=cmp("var f = func(): {}"),
    # arrow
    arrow_syntax=cmp("x->2"),
    arrow_conv=evals("x->2", "func(x): return 2"),
)