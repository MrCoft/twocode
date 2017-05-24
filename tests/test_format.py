from twocode.Tests import *

name_tests(
    # file indent
    # - making code indent itself indents the entire file
    file_indent=auto_cmp("0"),
    file_strip=cmp("\n0\n", "0"),
    file_empty_line=cmp("1\n\n2", "1\n2"),
    line_ws=cmp("1\n2 \n3", "1\n2\n3"),
    # block
    # - indent block does not end the line with a space
    # - support tabs and spaces
    block_enter=auto_cmp("if true:\n\t1\n\t2"),
    block_tabs=cmp(raw="if true:\n\t1\n\t2", result="if true:\n\t1\n\t2".replace("\t", " " * 4)),
    block_fallback=fails("if true:\n\t\t1\n\t2", "IndentationError"),
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
    block_single=auto_cmp("if true: 1"),
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
    if_single=auto_cmp("if true: 1"), # same thign as above
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
    #if_chain_empty=ast_fails(lambda node_types: node_types["stmt_if"](), InvalidIfChainEmpty),
    #test_if_cond_empty=ast_fails(lambda node_types: node_types["if_block"](), InvalidIfCondEmpty),
    # term tests
    term_index=auto_cmp("l[]"),
    term_call=auto_cmp("f()"),
)