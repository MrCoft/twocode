from twocode.Tests import *

name_tests(
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

    multiline_expr=cmp('''
        a +
            b
    ''', result="a + b"),
    multiline_invalid=cmp('''
        a
        -b
    ''', result="a\n-b"),

    empty_line=parses('''
        if true:
        \t1

        \t\t
        \t2
    ''', result="'if' WS LITERAL_boolean ':' EOL ENTER LITERAL_float EOL EOL EOL LITERAL_float LEAVE".split()),
    literal_int=parses("2", "LITERAL_int".split()),
    line_ext=parses("[\\\n]", "'[' ']'".split()),
)

# test - leave to negative indent
# test - } global error
# exactly one parse for 'if true:\n    1\n    2'