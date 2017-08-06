from twocode.parse.Lexer import LexLanguage
from twocode.parse.Grammar import Grammar
from twocode.parse.IndentParser import IndentParser
from twocode.parse.Context import Context as ParserContext
from twocode.parse.Console import Console as ConsoleBase
from twocode.utils.Nodes import map, switch, Var, regen_types
from twocode.Repr import gen_repr
import os
import sys

def twocode_lexer():
    lex_lang = LexLanguage()
    lex_lang.keywords = set('''
        var func type
        if else
        for in
        while break continue
        switch case default _
        with as
        throw try catch finally
        return
        super
        import from
        not and or
        macro
    '''.split())
    lex_lang.ops = {
        "ASSIGN": {'=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '&&=', '||='},
        "COMPARE": {'<', '>', '<=', '>=', '!=', '=='},
        "MATH": {'+', '-', '*', '/', '%', '&', '|', '^', '<<', '>>'},
        "FIX": {'++', '--'},
        "UNARY": {'+', '-', '~'},
    }
    lex_lang.raw = {'=', '(', ')', '[', ']', '{', '}', '.', ',', '<', '>', ':', '*', ';', '@', '-'}
    lex_lang.literals = {
        "null": 'null',
        "boolean": 'true|false',
        "integer": '0|[1-9][0-9]*',
        "float": '((0|[1-9][0-9]*)(\\.\\d*)?|\\.\\d+)([eE][+-]?\\d+)' + "|" + '((0|[1-9][0-9]*)(\\.\\d*)|\\.\\d+)(?!\\.)',
        "hexadecimal": '0[xX][0-9a-fA-F]+',
        "octal": '0[oO][0-7]+',
        "binary": '0[bB][01]+',
        "string": '\"([^\\\\\"\r\n]|\\\\.)*\"' + "|" + "\'([^\\\\\'\r\n]|\\\\.)*\'",
        "longstring": '\"\"\"([^\\\\]|\\\\.)*\"\"\"' + "|" + "\'\'\'([^\\\\]|\\\\.)*\'\'\'",
    }
    lex_lang.allow_ws = True
    lex_lang.indent_block = True
    return lex_lang

# ellipsis literal

def twocode_grammar():
    Rule = Grammar.Rule
    S = Grammar.Symbol
    Var = Grammar.Symbol.Var
    List = Grammar.Symbol.List
    grammar = Grammar()
    grammar.add_symbol("code", [
        Rule([Var("stmt")], "create"),
        Rule([Var("code"), "DELIM", S("stmt", var="stmt")], "append"),
        Rule(["DELIM", Var("code")], "lead"),
        Rule([Var("code"), "TRAIL"], "trail"),
    ])
    grammar.add_symbol("DELIM", [
        Rule(["EOL"]),
        Rule(["';'"], "INLINE"),
    ])
    grammar.add_symbol("TRAIL", [
        Rule(["WS"], "WS"),
        Rule(["';'"], "INLINE"),
    ])
    grammar.add_symbol("block", [
        Rule([S("block_list", var="block")]),
        Rule([Var("stmt")], "single"),
    ])
    grammar.add_symbol("block_list", [
        Rule(["ENTER", S("code", cond=True, var="block"), "LEAVE"], allow_ws=False),
        Rule(["'{'", S("code", cond=True, var="block"), "'}'"], "inline", allow_ws=False),
    ])
    grammar.add_symbol("imp", [
        Rule(["'import'", S("path", list=List(delim="','"), var="imports")]),
        Rule(["'from'", Var("path"), "'import'", S("path", list=List(delim="','"), var="imports")], "from"),
    ])
    grammar.add_symbol("path", [
        Rule([Var("path_list")]),
        Rule([Var("path_list"), "'as'", Var("id")], "name"),
    ])
    grammar.add_symbol("path_list", [
        Rule([S("path_item", list=List(delim="'.'"), var="path")], allow_ws=False),
    ])
    grammar.add_symbol("path_item", [
        Rule([Var("id")], "id"),
        Rule(["'*'"], "all"),
    ])
    grammar.add_symbol("type_ref", [
        Rule([Var("id")], "id"), # does not support dot path - or any expr
        Rule([Var("id"), "'<'", S("args", var="params"), "'>'"], "params"),
        Rule([S("type_ref", list=List(delim="','"), var="arg_types"), "ARROW", S("type_ref", list=List(delim="','"), var="return_types")], "func_def"), # broken, a->b->c
        # a->b
        # var x:()->()
        # var f:Float->Float
        # var f:Func<Float, Float>
        # func = obj(args=, code=, return_type=)
        Rule(["'('", S("type_ref", list=List(delim="','"), var="types"), "')'"], "tuple"),
    ])
    grammar.add_symbol("type_def", [
        Rule(["'type'", S("id", cond=True, var="id"), S("base", cond=True, var="base"), "':'", Var("block")]),
    ])
    grammar.add_symbol("base", [
        Rule(["'('", Var("type_ref"), "')'"]),
    ])
    grammar.add_symbol("decl", [
        Rule([Var("id"), S("decl_type", cond=True, var="type_ref")]),
        # Rule(["'('", S("decl", list=List(delim="','"), var="declares"), "')'"], "tuple"),
    ])
    grammar.add_symbol("decl_type", [
        Rule(["':'", Var("type_ref")]),
    ])
    grammar.add_symbol("func_def", [
        Rule(["'func'", S("id", cond=True, var="id"), "'('", S("func_arg", list=List(delim="','"), cond=True, var="args"), "')'", S("return_type", cond=True, var="return_type"), "':'", Var("block")]),
    ])
    grammar.add_symbol("func_arg", [
        Rule([S("pack", cond=True, var="pack"), S("'macro'", cond=True, var="macro"), Var("decl"), S("init", cond=True, var="init")]),
    ])
    grammar.add_symbol("return_type", [
        Rule(["ARROW", Var("type_ref")]),
    ])
    grammar.add_symbol("arrow_func", [
        Rule(["'('", S("func_arg", list=List(delim="','"), cond=True, var="args"), "')'", "ARROW", Var("expr")]),
        Rule([Var("id"), "ARROW", Var("expr")], "single"),
    ])
    grammar.add_symbol("range", [
        Rule([S("expr", var="min"), "ELLIPSIS", S("expr", var="max")]),
    ])
    grammar.add_symbol("in_block", [Rule(["'in'", Var("expr"), "':'", Var("block")])])
    grammar.add_symbol("for_loop", [Rule(["'for'", S("tuple", var="var"), "'in'", S("expr", var="iter"), "':'", Var("block")])])
    grammar.add_symbol("while_loop", [Rule(["'while'", S("expr", var="cond"), "':'", Var("block")])])
    grammar.add_symbol("if_chain", [Rule([Var("if_block"), S("else_if_block", list=List(), cond=True, var="else_if_blocks"), S("else_block", cond=True, var="else_block")])])
    grammar.add_symbol("if_block", [Rule(["'if'", S("expr", var="cond"), "':'", Var("block")])])
    grammar.add_symbol("else_if_block", [Rule(["'else'", Var("if_block")])])
    grammar.add_symbol("else_block", [Rule(["'else'", "':'", Var("block")])])
    grammar.add_symbol("try_chain", [Rule([Var("try_block"), S("catch_block", list=List(), cond=True, var="catch_blocks"), S("finally_block", cond=True, var="finally_block")])])
    grammar.add_symbol("try_block",     [Rule(["'try'", "':'", Var("block")])])
    grammar.add_symbol("catch_block",   [Rule(["'catch'", "':'", Var("block")])]) # catch e:Error: - !! ::
    grammar.add_symbol("finally_block", [Rule(["'finally'", "':'", Var("block")])])
    grammar.add_symbol("stmt", [
        Rule([Var("tuple")], "tuple"),
        Rule([Var("tuple"), S("assignment", list=List(), var="assign_chain")], "assign"),
        Rule(["'var'", S("decl", list=List(delim="','"), var="vars"), S("assignment", list=List(), cond=True, var="assign_chain")], "var"),
        Rule(["'return'", S("tuple", cond=True, var="tuple")], "return"),
        # Rule([Var("stmt"), "WS"], "trailing_ws"), # t_
        Rule(["'break'"], "break"),
        Rule(["'continue'"], "continue"),

        Rule([Var("imp")], "import"),
    ])
    grammar.add_symbol("assignment", [
        Rule([S("ASSIGN", var="op"), Var("tuple")]),
    ])
    grammar.add_symbol("tuple", [
        Rule([S("expr", list=List(delim="','"), var="expr_list")]),
        Rule([S("expr", list=List(delim="','"), var="expr_list"), "','"], "trail"),
    ])
    grammar.add_symbol("args", [
        Rule([S("call_arg", list=List(delim="','"), var="args")]), # surround also
    ])
    grammar.add_symbol("call_arg", [
        Rule([Var("expr")], "expr"),
        Rule([Var("id"), "'='", Var("expr")], "named"),
        Rule([Var("pack"), Var("expr")], "unpacked"),
    ])
    grammar.add_symbol("pack", [
        Rule(["'*'"], "args"),
        Rule(["DOUBLE_STAR"], "kwargs"),
    ])
    grammar.add_symbol("init", [
        Rule(["'='", Var("expr")]),
    ])
    grammar.add_symbol("DOUBLE_STAR", [
        Rule(["'*'", "'*'"], allow_ws=False),
    ])
    grammar.add_symbol("ARROW", [
        Rule(["'-'", "'>'"], allow_ws=False),
    ])
    grammar.add_symbol("ELLIPSIS", [
        Rule(["'.'", "'.'", "'.'"], allow_ws=False),
    ])
    grammar.add_symbol("expr", [
        Rule([Var("term")], "term"),
        Rule([S("expr", var="expr1"), S("MATH", var="op"), S("expr", var="expr2")], "math"),
        Rule([S("expr", var="expr1"), S("COMPARE", var="op"), S("expr", var="expr2")], "compare"),
        Rule([S("UNARY", var="op"), Var("term")], "unary"),
        Rule([S("FIX", var="op"), Var("term")], "prefix", allow_ws=False),
        Rule([Var("term"), S("FIX", var="op")], "postfix", allow_ws=False),

        Rule([S("expr", var="expr1"), "'and'", S("expr", var="expr2")], "and"),
        Rule([S("expr", var="expr1"), "'or'", S("expr", var="expr2")], "or"),
        Rule(["'not'", Var("expr")], "not"),
        Rule([S("expr", var="expr1"), "'in'", S("expr", var="expr2")], "in"),
        Rule([S("expr", var="expr1"), "'not'", "'in'", S("expr", var="expr2")], "not_in"),

        # Rule([S("block_list", var="block")], "block"),
        Rule([Var("if_chain")], "if"),
        Rule([Var("try_chain")], "try"),
        Rule([Var("for_loop")], "for"),
        Rule([Var("while_loop")], "while"),
        Rule([Var("in_block")], "in_block"),

        Rule([Var("func_def")], "func"),
        Rule([Var("type_def")], "type"),
        Rule([S("arrow_func", var="arrow")], "arrow"),

        Rule([Var("range")], "range"),
        Rule(["ELLIPSIS"], "ellipsis"),

        Rule(["'@'", Var("term"), Var("expr")], "decorator"),
        Rule(["'macro'", Var("code")], "macro"),
    ])
    grammar.add_symbol("map", [
        Rule([S("map_item", list=List(delim="','"), var="item_list")]),
        Rule([S("map_item", list=List(delim="','"), var="item_list"), "','"], "trail"),
    ])
    grammar.add_symbol("map_item", [
        Rule([S("expr", var="key"), "':'", S("expr", var="value")]),
    ])
    grammar.add_symbol("term", [
        Rule([Var("id")], "id"),
        Rule([Var("term"), "'.'", Var("id")], "access"),
        Rule([Var("term"), "'['", S("tuple", cond=True, var="tuple"), "']'"], "index"),

        Rule([S("LITERAL", var="literal")], "literal"),
        Rule([Var("term"), "'('", S("args", cond=True, var="args"), "')'"], "call"),
        Rule(["'('", S("tuple", cond=True, var="tuple"), "')'"], "tuple"),
        Rule(["'['", S("tuple", cond=True, var="tuple"), "']'"], "list"),
        Rule(["'['", Var("map"), "']'"], "map"),
    ])
    return grammar

# choose shortest path
# must not be cyclic though

# stmt_trailing_ws

from twocode.parse.Precedence import loops, form_prec as P, gen_valid_prec

def twocode_prec(rules):
    rules = loops(rules)

    prec = [
        *[P("_MATH", ops=layer.strip()) for layer in '''
            %
            * /
            + -
            << >>
            &
            ^
            |
        '''.strip().splitlines()],
        # P("_MATH"),

        #P("_ASSIGN"),
        # P("assignment_list"), # currently the operators are in an inner rule, making 8 and 10 meet on the same layer
        #P('='),

        P("'in'"),

        P("'func'"),
        P("'macro'"),
        P("'@'"),
    ]
    return gen_valid_prec(rules, prec)

    # right only applies to symmetric
    # why _MATH ?

    rule_map.update((gen_prec(rules, prec, [
        "_COMPARE in",
        "slice",
        "not",
        "and"
        "or",
    ])))
    # unary right
    # assign, \n if right

    return valid_op_prec(rules, rule_map, [])


from twocode.utils.Nodes import node_gen as node_gen_f
def node_gen(node_types, name, vars):
    node_type = node_gen_f(name, vars)
    node_types[name] = node_type
    return node_type

def transform_blocks(input_types):
    symbol = "block"
    node_types, type_map = regen_types(input_types)
    for type_name, input_type in input_types.items():
        node_type = node_types[type_name]
        node_type.vars = [Var(var.name, type=symbol) if var.type == symbol else var for var in node_type.vars]
    code = node_gen(node_types, "code", [Var("lines", type="stmt", list=True)])

    for node_type in \
            "block_list block_list_inline block_single".split() +\
            "code_create code_append code_lead code_trail".split():
        del node_types[node_type]

    type_map["code_create"] = lambda node: code([node.stmt])
    type_map["code_append"] = lambda node: code(node.code.lines + [node.stmt])
    type_map["code_lead"] = lambda node: node.code
    type_map["code_trail"] = lambda node: node.code
    type_map["block"] = lambda node: node.block
    type_map["block_single"] = lambda node: code([node.stmt])
    type_map["block_list"] = lambda node: node.block if node.block else code()
    type_map["block_list_inline"] = lambda node: node.block if node.block else code()
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_args(input_types):
    node_types, type_map = regen_types(input_types)
    func_arg = node_gen(node_types, "func_arg", [Var("id"), Var("type_ref", type="type_ref"), Var("value", type="expr"), Var("pack"), Var("macro")])
    call_arg = node_gen(node_types, "call_arg", [Var("value", type="expr"), Var("id"), Var("pack")])
    '''
        decl = node_gen([Var("id"), Var("type", type="type")])
        # decl_type

        grammar.add_symbol("decl", [
            Rule([Var("id"), S("decl_type", cond=True, var="type")]),
            # Rule(["'('", S("decl", list=List(delim="','"), var="declares"), "')'"], "tuple"),
        ])
    '''
    for node_type in \
            "call_arg_expr call_arg_named call_arg_unpacked".split() +\
            "pack_args pack_kwargs".split() +\
            "init return_type".split():
        del node_types[node_type]

    def pack_mode(node):
        if node is None:
            return None
        type_name = type(node).__name__
        if type_name == "pack_args":
            return "args"
        if type_name == "pack_kwargs":
            return "kwargs"
    type_map["func_arg"] = lambda node: func_arg(
        node.decl.id,
        node.decl.type_ref.type_ref if node.decl.type_ref else None,
        node.init.expr if node.init else None,
        pack_mode(node.pack),
        bool(node.macro),
    )
    type_map["call_arg_expr"] = lambda node: call_arg(node.expr)
    type_map["call_arg_named"] = lambda node: call_arg(node.expr, id=node.id)
    type_map["call_arg_unpacked"] = lambda node: call_arg(node.expr, pack=pack_mode(node.pack))
    type_map["term_call"] = lambda node: node_types["term_call"](node.term, node.args if node.args else node_types["args"]())
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_func(input_types):
    node_types, type_map = regen_types(input_types)
    func_def = node_gen(node_types, "func_def", [Var("id"), Var("args", type="func_arg", list=True), Var("return_type", type="type_ref"), Var("block", type="block")])

    type_map["func_def"] = lambda node: func_def(node.id, node.args, node.return_type.type_ref if node.return_type else None, node.block)
    type_map["arrow_func"] = lambda node: func_def(None, node.args, None, node_types["code"]([node_types["stmt_return"](node_types["tuple"]([node.expr]))]))
    type_map["arrow_func_single"] = lambda node: func_def(None, [node_types["func_arg"](node.id)], None, node_types["code"]([node_types["stmt_return"](node_types["tuple"]([node.expr]))]))
    type_map["expr_arrow"] = lambda node: node_types["expr_func"](node.arrow)
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_type(input_types):
    node_types, type_map = regen_types(input_types)
    type_def = node_gen(node_types, "type_def", [Var("id"), Var("base", type="type_ref"), Var("block", type="block")])

    type_map["type_def"] = lambda node: type_def(node.id, node.base.type_ref if node.base else None, node.block)
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_math(input_types):
    node_types, type_map = regen_types(input_types)
    expr_affix = node_gen(node_types, "expr_affix", [Var("term", type="term"), Var("op"), Var("affix")])
    for node_type in "expr_prefix expr_postfix".split():
        del node_types[node_type]

    type_map["expr_prefix"] = lambda node: expr_affix(node.term, node.op, "prefix")
    type_map["expr_postfix"] = lambda node: expr_affix(node.term, node.op, "postfix")
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_bool(input_types):
    node_types, type_map = regen_types(input_types)
    expr_bool = node_gen(node_types, "expr_bool", [Var("expr1", type="expr"), Var("op"), Var("expr2", type="expr")])
    for node_type in "expr_and expr_or expr_not_in".split():
        del node_types[node_type]

    type_map["expr_and"] = lambda node: expr_bool(node.expr1, "and", node.expr2)
    type_map["expr_or"] = lambda node: expr_bool(node.expr1, "or", node.expr2)
    type_map["expr_not_in"] = lambda node: node_types["expr_not"](node_types["expr_in"](node.expr1, node.expr2))
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

# bool, not, in, not in
'''
>>> not(2)
not (2)
>>> not(1 in 2)
not (1 in 2)
>>> not 1 in 2
not 1 in 2
>>>
'''

def transform_tuple(input_types):
    node_types, type_map = regen_types(input_types)
    tuple = node_gen(node_types, "tuple", [Var("expr_list", type="expr", list=True)])
    tuple_expr = node_gen(node_types, "tuple_expr", [Var("expr", type="expr")])
    map_type = node_gen(node_types, "map", [Var("item_list", type="map_item", list=True)])

    type_map["tuple"] = lambda node: tuple(node.expr_list) if len(node.expr_list) != 1 else tuple_expr(node.expr_list[0])
    type_map["tuple_trail"] = lambda node: tuple(node.expr_list)
    type_map["map"] = lambda node: map_type(node.item_list)
    type_map["map_trail"] = lambda node: map_type(node.item_list)
    type_map["term_index"] = lambda node: node_types["term_index"](node.term, node.tuple if node.tuple else tuple())
    type_map["term_tuple"] = lambda node: node_types["term_tuple"](node.tuple if node.tuple else tuple())
    type_map["term_list"] = lambda node: node_types["term_list"](node.tuple if node.tuple else tuple())
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_block_chains(input_types):
    node_types, type_map = regen_types(input_types)
    if_chain = node_gen(node_types, "if_chain", [Var("if_blocks", type="if_block", list=True), Var("else_block", type="block")])
    try_chain = node_gen(node_types, "try_chain", [Var("try_block", type="block"), Var("catch_blocks", type="catch_block", list=True), Var("finally_block", type="block")])

    type_map["if_chain"] = lambda node: if_chain(
        [node.if_block] + [else_if_block.if_block for else_if_block in node.else_if_blocks],
        node.else_block.block if node.else_block else None
    )
    type_map["try_chain"] = lambda node: try_chain(
        node.try_block.block,
        node.catch_blocks,
        node.finally_block.block if node.finally_block else None
    )
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_import(input_types):
    node_types, type_map = regen_types(input_types)
    imp = node_gen(node_types, "imp", [Var("imports", type="path", list=True), Var("module", list=True)])
    path = node_gen(node_types, "path", [Var("path", list=True), Var("name")])
    for node_type in "imp_from path_name path_list path_item_id path_item_all".split():
        del node_types[node_type]

    type_map["imp"] = lambda node: imp(node.imports)
    type_map["imp_from"] = lambda node: imp(node.imports, node.path.path)
    type_map["path"] = lambda node: path(node.path_list.path)
    type_map["path_name"] = lambda node: path(node.path_list.path, node.id)
    type_map["path_item_id"] = lambda node: node.id
    type_map["path_item_all"] = lambda node: "*"
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_repr(input_types):
    node_types, type_map = regen_types(input_types)
    for type_name, input_type in input_types.items():
        node_type = node_types[type_name]
        repr = gen_repr(node_type)
        if repr:
            node_type.__repr__ = repr
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

# maybe convert all to python values
def map_literals(context):
    import re
    pattern = context.lex_lang.literals["integer"]
    pattern = re.compile("({})$".format(pattern))
    literal = context.node_types["literal"]

    import codecs
    codec = codecs.getdecoder("unicode_escape")

    def map_literal(node):
        if pattern.match(node.value):
            return literal(node.value, "integer")
        if node.lit_type == "string":
            node.value = codec(node.value[1:-1])[0]
        if node.lit_type == "longstring":
            node.lit_type = "string"
            node.value = codec(node.value[3:-3])[0]
        return node
    type_map = {}
    type_map["literal"] = map_literal
    return map(leave=switch(type_map, key=lambda node: type(node).__name__))

class Parser(ParserContext):
    def __init__(self):
        super().__init__(twocode_lexer(), twocode_grammar())

        node_types = self.node_types
        node_types, t_blocks = transform_blocks(node_types)
        node_types, t_args = transform_args(node_types)
        node_types, t_func = transform_func(node_types)
        node_types, t_type = transform_type(node_types)
        node_types, t_math = transform_math(node_types)
        node_types, t_bool = transform_bool(node_types)
        node_types, t_tuple = transform_tuple(node_types)
        node_types, t_block_chains = transform_block_chains(node_types)
        node_types, t_import = transform_import(node_types)
        node_types, t_repr = transform_repr(node_types)
        self.node_types = node_types
        m_literals = map_literals(self)
        #node_types, t_int = transform_int(node_types)
        #node_types, t_op_prec = transform_op_prec(node_types)

        self.transforms += [
            t_blocks,
            t_args,
            t_func,
            t_type,
            t_math,
            t_bool,
            t_tuple,
            t_block_chains,
            t_import,
            t_repr,
            m_literals,
        ]

        parser = IndentParser()
        from twocode.parse.Parser import IncrementalParser
        parser.parser = IncrementalParser(self.rules)
        from twocode.parse.IndentParser import gen_valid, gen_insert
        parser.valid = gen_valid(twocode_prec(self.rules))
        parser.wrap_code, parser.insert = gen_insert(self.rules)
        self.parser = parser



    #def parse(self, code):
    #    self.parser.parse(self.lexer.parse(code))
    #    ast = self.parser.match()
    #    return ast

# import command inside

class Twocode:
    def __init__(self):
        self.parser = Parser()
        self.parse = self.parser.parse
        self.node_types = self.parser.node_types

        from twocode.Context import add_context
        add_context(self)

        import twocode.Utils
        self.builtins = twocode.Utils.Object()
        from twocode.context.Objects import add_objects
        add_objects(self)
        from twocode.context.BasicTypes import add_types
        add_types(self) # to builtins
        from twocode.context.Objects import sign_objects
        sign_objects(self)
        from twocode.context.Scope import add_scope
        add_scope(self)
        from twocode.context.BuiltIns import add_builtins
        add_builtins(self)
        from twocode.context.NodeTypes import add_node_types
        add_node_types(self)

        self.stack.insert(0, self.builtins)

        from twocode.context.Typing import add_typing
        add_typing(self)
    def shell_repr(self, obj):
        if hasattr(obj, "__this__") and obj.__this__ is None:
            obj = None
        else:
            obj = self.unwrap_value(self.builtins.repr.native(obj))
        return obj

import twocode.utils.Code
class Console(ConsoleBase):
    def __init__(self):
        super().__init__()
        self.twocode = Twocode()
        self.compile = lambda code: self.twocode.parse(code)
    @twocode.utils.Code.skip_traceback(0)
    def run(self, code):
        ast = self.compile(code)
        if ast is None:
            return True
        obj = self.twocode.eval(ast)
        if self.shell:
            obj = self.twocode.shell_repr(obj)
            if obj is not None:
                print(obj, file=sys.stderr, flush=True)
        return False
    def eval(self, code):
        ast = self.compile(code)
        # return ast
        return self.twocode.eval(ast)
#SyntaxError: Generator expression must be parenthesized if not sole argument
def compile(code):
    with open("main.rs", "w") as file:
        file.write(code)
    os.system("rustc main.rs")
    os.system("main.exe")

def main():
    console = Console()
    console.interact()
    return 0

if __name__ == "__main__":
    console = Console()
    context = console.twocode


    #console.twocode.eval(console.twocode.load("code/data/Node.2c"))
    #console.twocode.eval(console.twocode.load("code/parser/Lexer.2c"))

    # console.twocode.eval(console.twocode.load("code/parser/Lexer.2c"))
    # console.twocode.log_mode().__enter__()
    console.interact()
    #from languages.twocode.targets.Python import translate
    #print(translate(ast))

# is block a stmt? if so remove chains

"var a:C"
"var a:C<T>"
"var a:A->B"
"var a:(A,B)"

# tuple type

# or specify pattern matching, tuples, catch
# string interpolation
# expr arguments

# after that is playtime - redo this in the language. compile it in rust
# then we can try optimized shader/whatnot, and release it, or start redoing haxe code

# string format

# explicit types


# require empty line after indent
# decorators
# macros
# tests
# simple cpp

# 0.2







# type checking, conversions

# precedence
# rich operators

# .tuple.expr rm
# sort new twocode thing, rm load cmd

# eval takes envs
# scope_stack[-1]



# ast map

# : {} works but : { } does not



# <T> params, keys/values iterator, set from iterator


#  print from within, edit, to cpp, print cpp

# all reprs should print macro also

#(1,) ()

# format.args[0].name = "this"

# with -> in
# in enter exit
# in __scope__ if macro, gets the block
# in A: @cls var x = 2 (
# longstring inelegant

# regex, bytes in cpp

# immutable type, immutable object (not immutable but compiled) - native


# @include("re")
# cancel import if errors?
# hide inside class
# skip empty lines


# test for current macro bullshit
# test blocky
    # - errors




# sign all custom methods
# __new__


# term expr
# a ast wrapper AST Stack CodeStack
#

# [ ] scopes
# [ ] static, getters
# [ ] typing
# [ ] extra syntax

# comments


# haxe - regex
# simple tests
# a class-abstract split
# generated classes with fake children

#@id("loop") {
#}

# distribute native objects into fake packages
# -> comprehensions

# that class' fields (meta) have correct types
# static, getattr
# static - runtime interrupt
# package memory
# iterator - Intrange, fix, etc
# intiterator
# type not evaluating
# getter property

# .lang / .platform thing, the correct native imported as a fake module
# list uses the native

# native.
# code.native
# code.lang.native?
# .Lang
# twocode

# classes not remembered, methods not passed

# with is about stacking contexts, not about snatching the scope
# with EXPR: BLOCK

# stmt_list - try as {} or feed it parse from a file

# var a
# import from
# modules - import as, full_path
# fix prints
# Regex
# tuples

# fake modules - use the fact that they are alone, completely replace them


# finish scope
# __root__ - multiple values? or the dict?
# plugin types
# cover signatures
# tests
# fix indentparser

# class's slots typed?

# does the classic a() or b() work here?

# create partial cast

'''
a func that returns a type object
Func<a,b> reads as a->b
<> is just syntax to create an internal field __params__
    a weird scope visible for types of the class
    original - compatible, have to be types
func has none and is on request
'''

# in code.node_types would shorten the paths? or can i do a shady import like this?

'''
code.node_types
code.objects.Type
code.scope.Module

code.builtins
code.basic_types
'''

# module.copy()

# v3 - compiles, tests


# clear major stuff - context modules.

# possibly prec could be finished



# v4
# profile and fit types
# fake natives and paths of intrange

# super. __expr__ raises exc, returns a special term - accesses base type of current object
# Type.a(obj) also possible



# skip tuple? wouldnt it be nicer as OOP, if the expr->func step was skipped?

# another part of profiling is having everything reflected properly

# classes

# class.a = class.__fields__
# static access HOW?



# from _ import *
# also in
# module

# exc as string




# indentparser
# expr_func term still not fixed

# a.code
# a.__type__
# of func

# class getattr
# smells like internals -> getter
# func native
# null typing


# solve the obj case
# type_path
# add modules
# ip errors
# remove pack errors

# func type resolve fails on sources but name ref does not?
# cant even print types of nodes

# func access from class and getattr
    # printing a class should jump to its type. having type.__repr__ breaks this
# besides, inheritance! does access to a true value not depend on the slot it is in?

    # all references of uses, except super, refer to the top level of the class
    # we assume it is in a legal slot
    # raise exc if the call would be illegal for the slot

    # the base value type tossed around complex should be (value, type)

'''
C:\Python35\python.exe H:/Twocode/twocode/Twocode.py
>>> func f(n): return if n == 1: 1 else: n * f(n - 1)
null
>>> f
Traceback (most recent call last):

    tree = map[val](tree)
  File "H:\Twocode\twocode\Context.py", line 442, in term_id
    raise NameError("name {} is not defined".format(repr(id)))
NameError: name 'f' is not defined
>>> func f():{}
func(): {}
>>> f
func(): {}
>>> func f(n): {return if n == 1: 1 else n * f(n - 1)}
Traceback (most recent call last):
  File "H:/Twocode/twocode/Twocode.py", line 577, in <lambda>
    self.compile = lambda code: self.twocode.parse(code)
  File "H:\Twocode\twocode\parse\Context.py", line 20, in parse
    ast = self.parser.match()
  File "H:\Twocode\twocode\parse\IndentParser.py", line 47, in match
    raise Exception("\n".join([""] + [str(error) for error in self.errors]))
Exception:
can't parse <stmt> at: 'func' WS id("f") '(' id("n") ')' ':' WS '{' 'return' WS 'if' WS id("n") WS COMPARE("==") WS LITERAL_float("1") ':' WS LITERAL_float("1") WS 'else' WS id("n")
>>> func f(n): {return if n == 1: 1 else: n * f(n - 1)}
null
>>> f
func(): {}
>>> f(2)
Traceback (most recent call last):

    tree = map[val](tree)
  File "H:\Twocode\twocode\Context.py", line 472, in term_call
    scope = context.unpack_args(func, args)
  File "H:\Twocode\twocode\Context.py", line 99, in unpack_args
    raise SyntaxError("signature mismatch while unpacking arguments")
  File "<string>", line None
SyntaxError: signature mismatch while unpacking arguments
>>> f()
Traceback (most recent call last):

    tree = map[val](tree)
  File "H:\Twocode\twocode\Context.py", line 511, in expr_term
    type = obj.__type__
AttributeError: 'NoneType' object has no attribute '__type__'
>>>
'''