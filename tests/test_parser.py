from twocode.Tests import *

name_tests(
    # lexer
    # - regex edge cases
    # - raw have no data
    keyword_id=parses("ify", 'id("ify")'),
    keyword_end=parses("if", "'if'"),
    ws=parses(raw="  ", result="WS"),
    raw_repr=parses("var a = 2", """'var' WS id("a") WS '=' WS LITERAL_integer("2")"""),
    # literals
    int=parses("1", 'LITERAL_integer("1")'),
    float=parses(".5", 'LITERAL_float(".5")'),
    bool=parses("true", 'LITERAL_boolean("true")'),
    string_double=cmp('"abc"'),
    string_single=cmp("'abc'", '"abc"'),
    string_escape=cmp('"a\\nb"'),
    string_multiline=cmp('"""a\nb"""', '"a\\nb"'),
    # lists and tuples
    list=cmp("[1, 2]"),
    list_single=cmp("[1]"),
    list_empty=cmp("[]"),
    tuple=cmp("(1, 2)"),
    tuple_single=cmp("(1,)"),
    tuple_empty=cmp("()"),
    parens=cmp("(1)"),
    # indent parser
    # - indent block does not end the line with a space
    # - support tabs and spaces
    indent_enter=cmp("if true:\n\t1\n\t2"),
    indent_tabs=cmp(raw="if true:\n\t1\n\t2", result="if true:\n\t1\n\t2".replace("\t", " " * 4)),
    indent_align=compiles("""
        a = [
                0,
            1 + 2,
        ]
    """),
    indent_order=fails(raw="[\n{}1,\n]".format(" " * 4 + "\t"), error='IndentationError: spaces followed by tabs'),
    indent_consistent=fails(raw="if true:\n{}1\nif false:\n{}2".format(" " * 4, "\t"), error="IndentationError: inconsistent indentation('\t', was '    ')"),
    indent_mixed=fails(raw="if true:\n\t1\n\t2".replace("\t", " " * 4 + "\t"), error='IndentationError: mixed indentation'),
    indent_odd_space=fails(raw="if true:\n\t1\n\t2".replace("\t", " " * 5), error='IndentationError: odd number of spaces'),
    indent_odd_tab=fails(raw="if true:\n\t1\n\t2".replace("\t", " " * 5), error='IndentationError: multiple tabs'),

    # exprs
    math=cmp("1 + 2"),
    unary=cmp("-1"),
    code=cmp("{}"),

    empty_line=parses("""
        if true:
        \t1

        \t\t
        \t2
    """, result="""'if' WS LITERAL_boolean("true") ':' EOL ENTER("    ") LITERAL_integer("1") EOL EOL EOL LITERAL_integer("2") LEAVE"""),
    line_ext=parses("[\\\n]", "'[' ']'"),

    lines_cont=cmp("1 +\n2", "1 + 2"),
    lines_indent=cmp("1 +\n\t2", "1 + 2"),
    lines_split=cmp("1\n+ 2", "1\n+2"),
)

# the [] block thingy

# stmt_trail

# unexpected indent
# test - leave to negative indent
# test - } global error
#    indent_sane=fails("if true:\n\t\t1\n\t2", "IndentationError: indent not sane"),
# infinite loop on EOL EOL or LEAVE EOL
#
"""
    lex_lang.literals = [
        "boolean": 'true|false',
        "integer": '0|[1-9][0-9]*',
        "hexadecimal": '0[xX][0-9a-fA-F]+',
        "octal": '0[0-7]+',
        "binary": '0[bB][01]+',
        "string": r'\"((\\\")*[^\"\r\n]?)*\"',
    ]
"""
# ;;;
# func():{1;2;}
# {1;}

# """a"""b"""c"""
# 0.__type__

# class A: { func f(): return 2 }

# all of these to some eval as well


# " vs ' wraps? for short? python algo

# expr_block, valid and invalid
"""
if 0:
    var x = 3
    for a in b: 0
    print(0)
l = [0, 1]

that invalid statements are erased, it does not form a single stmt

iftrue:
    1

that a failed stmt does not just insert the contents, or that it makes the next stmt fail
"""

# can't parse <stmt> at: 'func' '(' ')' '-' '>' id("List") '<' id("Tuple") '<' id("K") ',' id("V") MATH(">>") ':'

# comments
# skip empty lines

# test blocky
    # - errors

    # type_func not type_func_Def

# with block
# inline if for while
# try catch