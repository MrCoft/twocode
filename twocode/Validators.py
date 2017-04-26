from twocode.Tests import *
import twocode.utils.Code
'''
a +
    b

a
-b
'''

tests_parser = name_tests("parser",
    keyword_id=parses("ify", "ID".split()),
    keyword_end=parses("if", "'if'".split()),

    a=fails(raw=''' # dedent
        if true:
            \t1
    '''),

    int=auto_cmp("1"),
    bool=auto_cmp("true"),
    string=auto_cmp('"abc"'),
    list=auto_cmp("[1, 2]"),
    list_single=auto_cmp("[1]"),
    list_empty=auto_cmp("[]"),

    tuple=auto_cmp("(1, 2)"),
    tuple_single=auto_cmp("(1,)"),
    tuple_empty=auto_cmp("()"),
    parens=auto_cmp("(1)"),



    math=auto_cmp("1 + 2"),
    unary=auto_cmp("-1"),

    code=auto_cmp("{}"),
    ws=parses(raw="  ", result="WS".split()),
)

class InvalidIfChainEmpty(Exception): pass
def valid_if_chain(node):
    type_name = type(node).__name__
    if type_name == "stmt_if":
        if not node.if_blocks:
            raise InvalidIfChainEmpty()
class InvalidIfCondEmpty(Exception): pass
def valid_if_block(node):
    type_name = type(node).__name__
    if type_name == "if_block":
        if not node.cond:
            raise InvalidIfCondEmpty()
tests_format = name_tests("format",
    # file indent
    # - making code indent itself indents the entire file
    file_indent=auto_cmp("0"),
    file_strip=cmp("\n0\n", "0"),
    file_empty_line=cmp("1\n\n2", "1\n2"),
    line_ws=cmp("1\n2 \n3", "1"),
    # block
    # - indent block does not end the line with a space
    # - support tabs and spaces
    block_enter=auto_cmp("if true:\n\t1\n\t2"),
    block_tabs=cmp(raw="if true:\n\t1\n\t2", result="if true:\n\t1\n\t2".replace("\t", " " * 4)),
    block_fallback=fails("if true:\n\t\t1\n\t2", IndentationError),
    block_align=compiles('''
        a = [
                0,
            1 + 2,
        ]
    '''),
    block_mixed=fails(raw="if true:\n{}1".format(" " * 4 + "\t")),
    block_odd=fails(raw="if true:\n{}1".format(" " * 3)),
    block_consistent=fails(raw="if true:\n{}1\nif false:\n{}2".format(" " * 4, "\t")),
    empty_line=cmp('''
        if true:
        \t1

        \t\t
        \t2
    ''', result="if true:\n\t1\n\t2"),
    # inline block
    # - inline needs an extra space to not do :{}
    # - margin spaces
    # - one-liners are inlined
    block_single=auto_cmp("if true: { 1 }"),
    # empty block
    # - code is conditional
    # - margin spaces in an empty block
    block_empty=auto_cmp("if true: {}"),
    # if-else blocks
    if_else_blocks=auto_cmp('''
        if a:
            a
        else if b:
            b
        else if c:
            c
        else:
            d
    '''),
    # inline format
    # - unwrap is forced for a chain
    # - empty is always {}
    if_inline=auto_cmp("if true: {}"),
    if_single=auto_cmp("if true: { 1 }"),
    if_multiple=auto_cmp('''
        if true:
            1
            2
    '''),
    if_unwrap=auto_cmp('''
        if true:
            1
        else if false:
            2
    '''),
    if_force_empty=auto_cmp('''
        if true: {}
        else if false:
            2
    '''),
    if_else=auto_cmp('''
        if true: {}
        else: {}
    '''),
    if_else_if=auto_cmp('''
        if true: {}
        else if false: {}
    '''),
    if_chain_empty=ast_fails(lambda node_types: node_types["stmt_if"](), InvalidIfChainEmpty),
    test_if_cond_empty=ast_fails(lambda node_types: node_types["if_block"](), InvalidIfCondEmpty),
    # term tests
    term_index=auto_cmp("l[]"),
    term_call=auto_cmp("f()"),
)

"var a:C"
"var a:C<T>"
"var a:A->B"
"var a:(A,B)"

# ;;;
# validators are currently just tests
 # context - an interpreter? not exec now
 # support \EOL

# exactly one parse for 'if true:\n    1\n    2'

# empty lines work!
    # but not for str full er

class InvalidPack(Exception): pass
# maybe add commentary to Invalid, or gen it, or print the ast
def pack_level(arg):
    if not arg.pack: return 0
    if arg.pack == "args": return 1
    if arg.pack == "kwargs": return 2
def valid_pack(node):
    type_name = type(node).__name__
    if type_name == "func":
        level = 0
        for arg in node.args:
            arg_pack = pack_level(arg)
            if arg_pack < level:
                raise InvalidPack()
            else:
                level = arg_pack
class InvalidUnpack(Exception): pass
def unpack_level(arg):
    if arg.ID: return 2
    if not arg.pack: return 0
    if arg.pack == "args": return 1
    if arg.pack == "kwargs": return 2
def valid_unpack(node):
    type_name = type(node).__name__
    if type_name == "args":
        level = 0
        for arg in node.args:
            arg_pack = unpack_level(arg)
            if arg_pack < level:
                raise InvalidUnpack()
            else:
                level = arg_pack
tests_func = name_tests("func",
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
    pack_arg=fails("func id(*args, pos): {}", InvalidPack),
    pack_kwarg=fails("func id(**kwargs, *args): {}", InvalidPack),
    # args unpacking
    unpack=auto_cmp("f(*args, **kwargs, pos=id, **kwargs2)"),
    unpack_arg=fails("f(*args, pos)", InvalidUnpack),
    unpack_kwarg=fails("f(**kwargs, *args)", InvalidUnpack),
    unpack_pos=fails("f(pos=id1, id2)", InvalidUnpack),
    # stmt
    stmt=auto_cmp("var f = func(): {}"),
)

# func does not write to builtins

tests_class = name_tests("class",
    # syntax,
    syntax=auto_cmp("class A: {}"),
    anon=auto_cmp("class: {}"),
    # stmt
    stmt=auto_cmp("var A = class: {}"),
)

validators = [validator for valid_name, validator in globals().copy().items() if valid_name.startswith("valid_")]
def validate_tb_layer(ast):
    for validator in validators:
        validator(ast)
@twocode.utils.Code.skip_traceback(2)
def validate(ast):
    validate_tb_layer(ast)
    for child in ast.children:
        validate(child)

if __name__ == "__main__":
    from utils.UnitTest import unit_test ## port to git
    import twocode.Validators
    unit_test(twocode.Validators)