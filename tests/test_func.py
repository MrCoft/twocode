from twocode.Tests import *

name_tests(
    # syntax
    syntax=auto_cmp("func id(): {}"),
    syntax_args=auto_cmp("func id(a:A = 1, b:B = 2)->C: {}"),
    # format
    format_enter=auto_cmp("func id():\n\t1\n\t2"),
    format_single=auto_cmp("func id(): { 1 }"),
    format_strip=cmp("func id(): {;0;}", "func id(): { 0 }"),
    format_anon=auto_cmp("func(): {}"),
    # args packing
    pack=auto_cmp("func id(pos, *args, **kwargs): {}"),
    pack_arg=fails("func id(*args, pos): {}", "InvalidPack"),
    pack_kwarg=fails("func id(**kwargs, *args): {}", "InvalidPack"),
    # args unpacking
    unpack=auto_cmp("f(*args, **kwargs, pos=id, **kwargs2)"),
    unpack_arg=fails("f(*args, pos)", "InvalidUnpack"),
    unpack_kwarg=fails("f(**kwargs, *args)", "InvalidUnpack"),
    unpack_pos=fails("f(pos=id1, id2)", "InvalidUnpack"),
    # stmt
    stmt=auto_cmp("var f = func(): {}"),
)