from twocode.Tests import *

name_tests(
    # file indent
    # - making code indent itself indents the entire file
    file_indent=cmp("0"),
    file_strip=cmp("\n0\n", "0"),
    file_empty_line=cmp("1\n\n2", "1\n2"),
    line_ws=cmp("1\n2 \n3", "1\n2\n3"),
    # inline block
    # - inline needs an extra space to not do :{}
    # - margin spaces
    # - one-liners are inlined
    block_single=cmp("if true: 1"),
    # empty block
    # - code is conditional
    # - margin spaces in an empty block
    block_empty=cmp("if true: {}"),
    # if-else blocks
    # - expand is forced for a chain
    # - empty is always {}
    if_else=cmp('''
        if true: {}
        else: {}
    '''),
    if_else_if=cmp('''
        if true: {}
        else if false: {}
    '''),
    if_multiple=cmp('''
        if true:
            1
            2
    '''),
    if_expand=cmp('''
        if true:
            1
        else if false:
            2
    '''),
    if_force_empty=cmp('''
        if true: {}
        else if false:
            2
    '''),
    # terms
    term_index=cmp("l[0]"),
    term_call=cmp("f()"),



    #if_chain_empty=ast_fails(lambda node_types: node_types["stmt_if"](), InvalidIfChainEmpty),
    #test_if_cond_empty=ast_fails(lambda node_types: node_types["if_block"](), InvalidIfCondEmpty),
    # term tests

)






# the ONLY sequence allowed is a = sequence, which assings the right value to all, FROM LEFT
# test that a = b = 2 sets both to 2 AND that a += anywhere fails AND that its not an expr AND that a=2 in arg has 1 parse

# disable expr_code, disable invalid lvalues

# ; sep not working
# test crements
# 1 + 2, 1 + parses, +1 fails
# []