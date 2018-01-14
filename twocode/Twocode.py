from twocode.parse.Lexer import LexLanguage
from twocode.parse.Grammar import Grammar
from twocode.parse.IndentParser import IndentParser
from twocode.parse.Context import Context as ParserContext
from twocode.parse.Console import Console as ConsoleBase
from twocode.utils.Nodes import map, switch, Var
from twocode.Repr import gen_repr
import os
import sys
import copy

def twocode_lexer():
    lex_lang = LexLanguage()
    lex_lang.keywords = """
        var func class
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
        ...
    """.split()
    lex_lang.ops = {
        "ASSIGN": "= += -= *= /= %= &= |= ^= <<= >>= **= //= &&= ||=".split(),
        "COMPARE": "== != < > <= >=".split(),
        "MATH": "+ - * / % & | ^ << >> ** //".split(),
        "FIX": "++ --".split(),
        "UNARY": "+ - ~".split(),
    }
    lex_lang.raw = "= ( ) [ ] { } . , < > : * ; @ - ?".split()
    lex_lang.literals = {
        "null": 'null',
        "boolean": 'true|false',
        "integer": '0|[1-9][0-9]*',
        "float": r'({})(?!\w)'.format('((0|[1-9][0-9]*)(\\.\\d*)?|\\.\\d+)([eE][+-]?\\d+)' + "|" + '((0|[1-9][0-9]*)(\\.\\d*)|\\.\\d+)(?!\\.)'),
        "hexadecimal": '0[xX][0-9a-fA-F]+',
        "octal": '0[oO][0-7]+',
        "binary": '0[bB][01]+',
        "string": '\"([^\\\\\"\r\n]|\\\\.)*\"' + "|" + "\'([^\\\\\'\r\n]|\\\\.)*\'",
        "longstring": '\"\"\"([^\\\\]|\\\\.)*?\"\"\"' + "|" + "\'\'\'([^\\\\]|\\\\.)*?\'\'\'",
    }
    lex_lang.allow_ws = True
    lex_lang.indent_block = True
    return lex_lang

# chokes on iter without the return
# ?args

def twocode_grammar():
    Rule = Grammar.Rule
    S = Grammar.Symbol
    Var = Grammar.Symbol.Var
    List = Grammar.Symbol.List
    grammar = Grammar()
    grammar.add_symbol("code", [
        Rule([Var("stmt")], "create"),
        Rule([Var("code"), "DELIM", S("stmt", var="stmt")], "append"),
        Rule(["TRAIL", Var("code")], "lead"),
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
        # its some elaborate thing? this, vs trail, vs definition in grammar ?!?!
        Rule(["ENTER", S("code", opt=True, var="block"), "LEAVE"], allow_ws=False),
        Rule(["'{'", S("code", opt=True, var="block"), "'}'"], "inline", allow_ws=False),
    ])
    grammar.add_symbol("imp", [
        Rule(["'import'", S("path", list=List(delim="','"), var="imports")]),
        Rule(["'from'", S("path_list", var="source"), "'import'", S("path", list=List(delim="','"), var="imports")], "from"),
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
    grammar.add_symbol("type", [
        Rule([Var("id")], "id"), # does not support dot path - or any expr
        Rule([Var("id"), "'<'", S("args", var="params"), "'>'"], "params"), # or Map<Tuple<K,V>>
        Rule([S("type", list=List(delim="','"), var="arg_types"), "ARROW", S("type", list=List(delim="','"), var="return_types")], "func"), # broken, a->b->c
        # a->b
        # var x:()->()
        # var f:Float->Float
        # var f:Func<Float, Float>
        # func = obj(args=, code=, return_type=)
        Rule(["'('", S("type", list=List(delim="','"), var="types"), "')'"], "tuple"),
    ])
    grammar.add_symbol("class_def", [
        Rule(["'class'", S("id", opt=True, var="id"), S("base", opt=True, var="base"), "':'", Var("block")]),
    ])
    grammar.add_symbol("base", [
        Rule(["'('", Var("type"), "')'"]),
    ])
    grammar.add_symbol("decl", [
        Rule([Var("id"), S("decl_type", opt=True, var="type")]),
        # Rule(["'('", S("decl", list=List(delim="','"), var="declares"), "')'"], "tuple"),
    ])
    grammar.add_symbol("decl_type", [
        Rule(["':'", Var("type")]),
    ])
    grammar.add_symbol("func_def", [
        Rule(["'func'", S("id", opt=True, var="id"), "'('", S("func_arg", list=List(delim="','"), opt=True, var="args"), "')'", S("return_type", opt=True, var="return_type"), "':'", Var("block")]),
    ])
    grammar.add_symbol("func_arg", [
        Rule([S("pack", opt=True, var="pack"), S("opt", opt=True, var="opt"), S("'macro'", opt=True, var="macro"), Var("decl"), S("init", opt=True, var="init")]),
        Rule(["'*'"], "star"),
    ])
    grammar.add_symbol("return_type", [
        Rule(["ARROW", Var("type")]),
    ])
    grammar.add_symbol("arrow_func", [
        Rule(["'('", S("func_arg", list=List(delim="','"), opt=True, var="args"), "')'", "ARROW", Var("expr")]),
        Rule([Var("id"), "ARROW", Var("expr")], "single"),
    ])
    grammar.add_symbol("range", [
        Rule([S("expr", var="min"), "ELLIPSIS", S("expr", var="max")]),
        # macro (@repr a)
        # DO DO this - precedence
    ])



    grammar.add_symbol("if_chain", [Rule([Var("if_block"), S("else_if_block", list=List(), opt=True, var="else_if_blocks"), S("else_block", opt=True, var="else_block")])])
    grammar.add_symbol("if_block", [Rule(["'if'", S("expr", var="cond"), "':'", Var("block")])])
    grammar.add_symbol("else_if_block", [Rule(["'else'", Var("if_block")])])
    grammar.add_symbol("else_block", [Rule(["'else'", "':'", Var("block")])])
    grammar.add_symbol("for_loop", [Rule(["'for'", S("tuple", var="var"), "'in'", S("expr", var="iter"), "':'", Var("block")])])
    grammar.add_symbol("while_loop", [Rule(["'while'", S("expr", var="cond"), "':'", Var("block")])])
    # grammar.add_symbol("")







    grammar.add_symbol("with_block", [Rule(["'with'", Var("expr"), S("named", opt=True, var=""), "':'", Var("block")])])
    grammar.add_symbol("in_block", [Rule(["'in'", Var("expr"), S("named", opt=True, var="rename"), "':'", Var("block")])])
    grammar.add_symbol("named", [
        Rule(["'as'", Var("id")]),
    ])




    grammar.add_symbol("try_chain", [Rule([Var("try_block"), S("catch_block", list=List(), opt=True, var="catch_blocks"), S("finally_block", opt=True, var="finally_block")])])
    grammar.add_symbol("try_block",     [Rule(["'try'", "':'", Var("block")])])
    grammar.add_symbol("catch_block",   [Rule(["'catch'", "':'", Var("block")])]) # catch e:Error: - !! ::
    grammar.add_symbol("finally_block", [Rule(["'finally'", "':'", Var("block")])])
    grammar.add_symbol("stmt", [
        Rule([Var("tuple")], "tuple"),
        Rule([Var("tuple"), S("assignment", list=List(), var="assign_chain")], "assign"),
        Rule(["'var'", S("decl", list=List(delim="','"), var="vars"), S("assignment", list=List(), opt=True, var="assign_chain")], "var"),
        Rule(["'return'", S("tuple", opt=True, var="tuple")], "return"),
        Rule([Var("stmt"), "WS"], "trail", allow_ws=False), # end?
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
    grammar.add_symbol("opt", [
        Rule(["'?'"]),
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
        Rule(["'...'"]),
    ])
    grammar.add_symbol("expr", [
        Rule([Var("term")], "term"),
        Rule([S("expr", var="expr1"), S("MATH", var="op"), S("expr", var="expr2")], "math"),
        Rule([S("expr", var="expr1"), S("COMPARE", var="op"), S("expr", var="expr2")], "compare"),
        Rule([S("UNARY", var="op"), Var("expr")], "unary"),
        Rule([S("FIX", var="op"), Var("term")], "prefix", allow_ws=False),
        Rule([Var("term"), S("FIX", var="op")], "postfix", allow_ws=False),

        Rule([S("expr", var="expr1"), "'and'", S("expr", var="expr2")], "and"),
        Rule([S("expr", var="expr1"), "'or'", S("expr", var="expr2")], "or"),
        Rule(["'not'", Var("expr")], "not"),
        Rule([S("expr", var="expr1"), "'in'", S("expr", var="expr2")], "in"),
        Rule([S("expr", var="expr1"), "'not'", "'in'", S("expr", var="expr2")], "not_in"),

        # Rule([S("block_list", var="block")], "block"),

        Rule([Var("if_chain")], "if"),
        Rule([Var("for_loop")], "for"),
        Rule([Var("while_loop")], "while"),

        Rule([Var("try_chain")], "try"),

        Rule([Var("with_block")], "with_block"),
        Rule([Var("in_block")], "in_block"),

        Rule([Var("func_def")], "func"),
        Rule([Var("class_def")], "class"),
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
        Rule([Var("term"), "'.'", Var("id")], "attr"),
        Rule([Var("term"), "'['", S("tuple", opt=True, var="tuple"), "']'"], "key"),

        Rule([S("LITERAL", var="literal")], "literal"),
        Rule([Var("term"), "'('", S("args", opt=True, var="args"), "')'"], "call"),
        Rule(["'('", S("tuple", opt=True, var="tuple"), "')'"], "tuple"),
        Rule(["'['", S("tuple", opt=True, var="tuple"), "']'"], "list"),
        Rule(["'['", Var("map"), "']'"], "map"),
    ])
    return grammar

# choose shortest path
# must not be cyclic though

# stmt_trailing_ws

from twocode.parse.Precedence import loops, form_prec as P, gen_valid_prec
# imports

def twocode_prec(rules):
    rules = loops(rules)

    prec = [
        *[P("_MATH", ops=layer.strip()) for layer in """
            %
            * /
            + -
            << >>
            &
            ^
            |
        """.strip().splitlines()],
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

# IP gives warnings on multiple parses

# 1 + 2 * 3
# transform_types, bool stuff, IndentParser
# no prints in context
# clear parser and its vars, here too

# [ ] IndentParser
# [ ] expr block
# [ ] cleared debug prints

def transform_types(input_types):
    node_types = {}
    from twocode.utils.Nodes import node_gen as node_gen_f
    def node_gen(name, vars):
        node_type = node_gen_f(name, vars)
        node_types[name] = node_type
        return node_type
    # STILL debatable!
    for type_name, input_type in input_types.items():
        node_gen(type_name, copy.deepcopy(input_type.vars))
    def gen_retype(node_type):
        def f(node):
            return node_type(**node.__dict__)
        return f
    type_map = {}
    for type_name, node_type in node_types.items():
        type_map[type_name] = gen_retype(node_type)

    # TYPES: blocks
    symbol = "block"
    for type_name, input_type in input_types.items():
        node_type = node_types[type_name]
        node_type.vars = [Var(var.name, type=symbol) if var.type == symbol else var for var in node_type.vars]
    code = node_gen("code", [Var("lines", type="stmt", list=True)])

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
    type_map["stmt_trail"] = lambda node: node.stmt

    # TYPES: args
    func_arg = node_gen("func_arg", [Var("id"), Var("type", type="type"), Var("default", type="expr"), Var("pack"), Var("macro")])
    call_arg = node_gen("call_arg", [Var("value", type="expr"), Var("id"), Var("pack")])
    """
        decl = node_gen([Var("id"), Var("type", type="type")])
        # decl_type

        grammar.add_symbol("decl", [
            Rule([Var("id"), S("decl_type", opt=True, var="type")]),
            # Rule(["'('", S("decl", list=List(delim="','"), var="declares"), "')'"], "tuple"),
        ])
    """
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
    def map_func_arg(node):
        arg = func_arg(
            node.decl.id,
            node.decl.type.type if node.decl.type else None,
            node.init.expr if node.init else None,
            pack_mode(node.pack),
            bool(node.macro),
        )
        if node.opt:
            if arg.default is not None:
                raise SyntaxError("optional argument with default value")
            arg.default = node_types["expr_term"](node_types["term_literal"](node_types["literal"]("null", "null")))
        return arg
    type_map["func_arg"] = map_func_arg
    type_map["call_arg_expr"] = lambda node: call_arg(node.expr)
    type_map["call_arg_named"] = lambda node: call_arg(node.expr, id=node.id)
    type_map["call_arg_unpacked"] = lambda node: call_arg(node.expr, pack=pack_mode(node.pack))
    type_map["term_call"] = lambda node: node_types["term_call"](node.term, node.args if node.args else node_types["args"]())

    # TYPES: func
    func_def = node_gen("func_def", [Var("id"), Var("args", type="func_arg", list=True), Var("return_type", type="type"), Var("block", type="block")])

    type_map["func_def"] = lambda node: func_def(node.id, node.args, node.return_type.type if node.return_type else None, node.block)
    type_map["arrow_func"] = lambda node: func_def(None, node.args, None, node_types["code"]([node_types["stmt_return"](node_types["tuple_expr"](node.expr))]))
    type_map["arrow_func_single"] = lambda node: func_def(None, [node_types["func_arg"](node.id)], None, node_types["code"]([node_types["stmt_return"](node_types["tuple_expr"](node.expr))]))
    type_map["expr_arrow"] = lambda node: node_types["expr_func"](node.arrow)

    # TYPES: class
    class_def = node_gen("class_def", [Var("id"), Var("base", type="type"), Var("block", type="block")])

    type_map["class_def"] = lambda node: class_def(node.id, node.base.type if node.base else None, node.block)

    # TYPES: math
    expr_affix = node_gen("expr_affix", [Var("term", type="term"), Var("op"), Var("affix")])
    for node_type in "expr_prefix expr_postfix".split():
        del node_types[node_type]

    type_map["expr_prefix"] = lambda node: expr_affix(node.term, node.op, "prefix")
    type_map["expr_postfix"] = lambda node: expr_affix(node.term, node.op, "postfix")

    # TYPES: bool
    expr_bool = node_gen("expr_bool", [Var("expr1", type="expr"), Var("op"), Var("expr2", type="expr")])
    for node_type in "expr_and expr_or expr_not_in".split():
        del node_types[node_type]

    type_map["expr_and"] = lambda node: expr_bool(node.expr1, "and", node.expr2)
    type_map["expr_or"] = lambda node: expr_bool(node.expr1, "or", node.expr2)
    type_map["expr_not_in"] = lambda node: node_types["expr_not"](node_types["expr_in"](node.expr1, node.expr2))

    # TYPES: tuple
    tuple = node_gen("tuple", [Var("expr_list", type="expr", list=True)])
    tuple_expr = node_gen("tuple_expr", [Var("expr", type="expr")])
    map_type = node_gen("map", [Var("item_list", type="map_item", list=True)])

    type_map["tuple"] = lambda node: tuple(node.expr_list) if len(node.expr_list) != 1 else tuple_expr(node.expr_list[0])
    type_map["tuple_trail"] = lambda node: tuple(node.expr_list)
    type_map["map"] = lambda node: map_type(node.item_list)
    type_map["map_trail"] = lambda node: map_type(node.item_list)
    type_map["term_key"] = lambda node: node_types["term_key"](node.term, node.tuple if node.tuple else tuple())
    type_map["term_tuple"] = lambda node: node_types["term_tuple"](node.tuple if node.tuple else tuple())
    type_map["term_list"] = lambda node: node_types["term_list"](node.tuple if node.tuple else tuple())

    # TYPES: block chains
    if_chain = node_gen("if_chain", [Var("if_blocks", type="if_block", list=True), Var("else_block", type="block")])
    try_chain = node_gen("try_chain", [Var("try_block", type="block"), Var("catch_blocks", type="catch_block", list=True), Var("finally_block", type="block")])

    type_map["if_chain"] = lambda node: if_chain(
        [node.if_block] + [else_if_block.if_block for else_if_block in node.else_if_blocks],
        node.else_block.block if node.else_block else None
    )
    type_map["try_chain"] = lambda node: try_chain(
        node.try_block.block,
        node.catch_blocks,
        node.finally_block.block if node.finally_block else None
    )

    # TYPES: import
    imp = node_gen("imp", [Var("imports", type="path", list=True), Var("source", list=True)])
    path = node_gen("path", [Var("path", list=True), Var("name")])
    for node_type in "imp_from path_name path_list path_item_id path_item_all".split():
        del node_types[node_type]

    type_map["imp"] = lambda node: imp(node.imports)
    type_map["imp_from"] = lambda node: imp(node.imports, node.source.path)
    type_map["path"] = lambda node: path(node.path_list.path)
    type_map["path_name"] = lambda node: path(node.path_list.path, node.id)
    type_map["path_item_id"] = lambda node: node.id
    type_map["path_item_all"] = lambda node: "*"

    # TYPES: repr
    for type_name, node_type in node_types.items():
        repr = gen_repr(node_type)
        if repr:
            node_type.__repr__ = repr

    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

# bool, not, in, not in
"""
>>> not(2)
not (2)
>>> not(1 in 2)
not (1 in 2)
>>> not 1 in 2
not 1 in 2
>>>
"""

def map_literals(parser):
    import re
    pattern = parser.lex_lang.literals["integer"]
    pattern = re.compile("({})$".format(pattern))
    literal = parser.node_types["literal"]
    import codecs
    codec = codecs.getdecoder("unicode_escape")

    def map_literal(node):
        if pattern.match(node.value):
            return literal(node.value, "integer") #?
        if node.type == "string":
            node.value = codec(node.value[1:-1])[0]
        if node.type == "longstring":
            node.type = "string"
            node.value = codec(node.value[3:-3])[0]
        #if node.type == "string": #
        #    node.value = re.sub("\\\n\r", "", node.value)
        return node
    type_map = {}
    type_map["literal"] = map_literal
    return map(leave=switch(type_map, key=lambda node: type(node).__name__))

class Parser(ParserContext):
    def __init__(self):
        super().__init__(twocode_lexer(), twocode_grammar())

        node_types = self.node_types
        node_types, transform = transform_types(node_types)
        self.node_types = node_types
        m_literals = map_literals(self)
        #node_types, t_int = transform_int(node_types)
        #node_types, t_op_prec = transform_op_prec(node_types)

        self.transforms += [
            transform,
            m_literals,
        ]

        parser = IndentParser()
        from twocode.parse.Parser import IncrementalParser
        parser.parser = IncrementalParser(self.rules)
        from twocode.parse.IndentParser import gen_valid_indent, gen_insert
        parser.valids.append(gen_valid_indent())
        parser.valids.append(twocode_prec(self.rules))
        parser.wrap_code, parser.insert = gen_insert(self.rules)
        self.parser = parser

        # parser.parser.parser


    #def parse(self, code):
    #    self.parser.parse(self.lexer.parse(code));
    #    ast = self.parser.match()
    #    return ast

# import command inside
# from expr import *
# defined(scope)->scope

# closure might very well be printable
# and an appropriate repr of any mentioned variables - eg default=[]
# so you can do in a.b.c: in scope(default=[]): func() and just skip the closure thing altogether


class Twocode:
    def __init__(self):
        """
            SELF-ASSEMBLY PROBLEM:
            functions without signatures aren't inherited and can't be called
            but the best way to set a signature is to transplant it
            from a function you get from eval(parse(sign))
            but that needs scope with signed methods to work

            OLD DEPENDENCY HELL:
            caused by accessing objects that are introduced later

            objects require Code
            basic types define hash, needed by scope creation
            node_types have trouble looking up their names
            scope creation requires other types
            sign requires basics and scope
            scope_types requires typed hashes

            scope methods signed manually for sign to work:
            __init__ of Scope, Module, Env
            __getattr__ of Scope, Module
            declare of Scope, Module

            the tangle would be weaker if untyped signatures worked
            setup.flush_typing() when they don't
        """

        self.parser = Parser()
        self.parse = self.parser.parse

        from twocode.Context import add_context
        add_context(self)
        from twocode.context.Setup import add_setup
        add_setup(self)
        from twocode.context.Scope import scope_builtins
        scope_builtins(self)

        from twocode.context.Objects import add_objects
        add_objects(self) # NOTE: required by everything else
        from twocode.context.BasicTypes import add_basics
        add_basics(self)
        from twocode.context.Operators import add_operators
        add_operators(self)
        from twocode.context.Builtins import add_builtins
        add_builtins(self)
        from twocode.context.NodeTypes import add_node_types
        add_node_types(self)
        from twocode.context.Scope import add_scope
        add_scope(self)

        from twocode.context.Typing import add_typing
        add_typing(self)
        from twocode.context.Logging import add_logging
        add_logging(self)

        from twocode.context.Scope import init_scope
        init_scope(self)
        from twocode.context.Scope import scope_types
        scope_types(self)
        from twocode.context.Scope import add_ref
        add_ref(self)
        # self.setup.end()

import twocode.utils.Code
class Console(ConsoleBase):
    def __init__(self, context=None):
        super().__init__()
        if context is None: context = Twocode()
        self.twocode = context
        self.compile = lambda code: self.twocode.parse(code)
    @twocode.utils.Code.skip_traceback(0)
    def run(self, code):
        ast = self.compile(code)
        if ast is None:
            return True
        obj = self.twocode.eval(ast)
        if self.shell:
            obj = self.twocode.shell_repr(obj)
            # why invisible error?
            if obj is not None:
                print(obj, file=sys.stderr, flush=True)
        return False
    def eval(self, code):
        ast = self.compile(code)
        return self.twocode.eval(ast)
#SyntaxError: Generator expression must be parenthesized if not sole argument
def compile(code):
    with open("main.rs", "w") as file:
        file.write(code)
    os.system("rustc main.rs")
    os.system("main.exe")
    # Utils.cmd

def main():
    console = Console()
    console.interact()
    return 0

if __name__ == "__main__":

    #import bprofile
    #with bprofile.BProfile("profile.png"):

    import time


    console = Console()
    context = console.twocode

    # start = time.time()

    # context.imp("test_js")

    # print(time.time() - start)
    console.interact()
    #from languages.twocode.targets.Python import translate
    #print(translate(ast))