from twocode.parse.Lexer import LexLanguage
from twocode.parse.Grammar import Grammar
from twocode.parse.Parser import IncrementalParser
from twocode.parse.Context import Context as ParserContext
from twocode.parse.Console import Console as ConsoleBase
from twocode.utils.Nodes import map, switch, node_gen, Var, regen_types
from twocode.Repr import gen_repr
from twocode.Validators import validate
from twocode.Context import add_context
import os
import sys

def twocode_lexer():
    lex_lang = LexLanguage()
    lex_lang.keywords = set('''
        var func class
        if else
        for in
        while break continue
        switch case default _
        with as
        throw try catch finally
        return
        super
        import
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
        "float": '((0|[1-9][0-9]*)(\\.\\d*)?|\\.\\d+)([eE][+-]?\\d+)?',
        "hexadecimal": '0[xX][0-9a-fA-F]+',
        "octal": '0[oO][0-7]+',
        "binary": '0[bB][01]+',
        "string": r'\"((\\\")*[^\"\r\n]?)*\"|\"((\\\")*[^\"\r\n]?)*\"',
    }
    lex_lang.allow_ws = True
    lex_lang.indent_block = True
    return lex_lang

# solve indent pairs and indent validator

def twocode_grammar():
    Rule = Grammar.Rule
    S = Grammar.Symbol
    Var = Grammar.Symbol.Var
    List = Grammar.Symbol.List
    grammar = Grammar()

    grammar.add_symbol("code", [
        Rule([Var("stmt")], "create"),
        Rule([Var("code"), "DELIM", S("stmt", var="stmt")], "append"),
        Rule(["TRAIL", Var("code")], "lead"), # was delim
        Rule([Var("code"), "TRAIL"], "trail"),
    ])
    grammar.add_symbol("DELIM", [
        Rule(['EOL']),
        Rule(["';'"], "INLINE"),
    ])
    grammar.add_symbol("TRAIL", [
        Rule(['EOL']),
        Rule(["';'"], "INLINE"),
        Rule(["WS"], "WS")
    ])
    grammar.add_symbol("block", [
        Rule([S("block_list", var="block")]),
        Rule([Var("stmt")], "single"),
    ])
    grammar.add_symbol("block_list", [
        Rule(["ENTER", S("code", var="block"), "LEAVE"], allow_ws=False),
        Rule(["'{'", S("code", cond=True, var="block"), "'}'"], "inline", allow_ws=False),
    ])
    grammar.add_symbol("type", [
        Rule([Var("ID")], "ID"),
        Rule([Var("ID"), "'<'", S("args", var="params"), "'>'"], "params"),
        Rule([S("type", list=List("','"), var="arg_types"), "ARROW", S("type", list=List("','"), var="return_types")], "func"), # broken, a->b->c
        Rule(["'('", S("type", list=List(delim="','"), var="types"), "')'"], "tuple"),
    ])
    grammar.add_symbol("class", [
        Rule(["'class'", S("ID", cond=True, var="ID"), S("parent", cond=True, var="parent"), "':'", Var("block")]),
    ])
    grammar.add_symbol("parent", [
        Rule(["'('", Var("type"), "')'"]),
    ])
    grammar.add_symbol("decl", [
        Rule([Var("ID"), S("decl_type", cond=True, var="type")]),
        # Rule(["'('", S("decl", list=List(delim="','"), var="declares"), "')'"], "tuple"),
    ])
    grammar.add_symbol("decl_type", [
        Rule(["':'", Var("type")]),
    ])
    grammar.add_symbol("func", [
        Rule(["'func'", S("ID", cond=True, var="ID"), "'('", S("func_arg", list=List(delim="','"), cond=True, var="args"), "')'", S("return_type", cond=True, var="return_type"), "':'", Var("block")]),
    ])
    grammar.add_symbol("func_arg", [
        Rule([S("pack", cond=True, var="pack"), Var("decl"), S("init", cond=True, var="init")]),
    ])
    grammar.add_symbol("return_type", [
        Rule(["ARROW", Var("type")]),
    ])
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
        Rule(["'var'", S("decl", list=List(delim="','"), var="vars"), S("assignment", list=List(), var="assign_chain")], "var"),
        Rule(["'return'", S("tuple", cond=True, var="tuple")], "return"),
        # Rule([Var("stmt"), "WS"], "trailing_ws"), # t_
        Rule(["'break'"], "break"),
        Rule(["'continue'"], "continue"),
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
        Rule([Var("ID"), "'='", Var("expr")], "named"),
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

        Rule([S("block_list", var="block")], "block"),
        Rule([Var("if_chain")], "if"),
        Rule([Var("try_chain")], "try"),
        Rule([Var("for_loop")], "for"),
        Rule([Var("while_loop")], "while"),

        Rule([Var("func")], "func"),
        Rule([Var("class")], "class"),
    ])
    grammar.add_symbol("term", [
        Rule([Var("ID")], "ID"),
        Rule([Var("term"), "'.'", Var("ID")], "access"),
        Rule([Var("term"), "'['", S("tuple", cond=True, var="tuple"), "']'"], "index"),

        Rule([S("LITERAL", var="literal")], "literal"),
        Rule([Var("term"), "'('", S("args", cond=True, var="args"), "')'"], "call"),
        Rule(["'('", S("tuple", cond=True, var="tuple"), "')'"], "tuple"),
        Rule(["'['", S("tuple", cond=True, var="tuple"), "']'"], "array"),
    ])
    return grammar

# choose shortest path
# must not be cyclic though

# stmt_trailing_ws

# var rename?

def transform_blocks(input_types):
    symbol = "block"
    node_types, type_map = regen_types(input_types)
    for type_name, input_type in input_types.items():
        node_type = node_types[type_name]
        node_type.vars = [Var(var.name, type=symbol) if var.type == symbol else var for var in node_type.vars]
    code = node_gen([Var("lines", type="stmt", list=True)], "code")
    node_types["code"] = code
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
    type_map["block_list"] = lambda node: node.block
    type_map["block_list_inline"] = lambda node: node.block if node.block else code()
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_args(input_types):
    node_types, type_map = regen_types(input_types)
    func_arg = node_gen([Var("ID"), Var("type", type="type"), Var("value", type="expr"), Var("pack")], "func_arg")
    node_types["func_arg"] = func_arg
    call_arg = node_gen([Var("value", type="expr"), Var("ID"), Var("pack")], "call_arg")
    node_types["call_arg"] = call_arg
    '''
        decl = node_gen([Var("ID"), Var("type", type="type")])
        # decl_type

        grammar.add_symbol("decl", [
            Rule([Var("ID"), S("decl_type", cond=True, var="type")]),
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
        node.decl.ID,
        node.decl.type.type if node.decl.type else None,
        node.init.expr if node.init else None,
        pack_mode(node.pack)
    )
    type_map["call_arg_expr"] = lambda node: call_arg(node.expr)
    type_map["call_arg_named"] = lambda node: call_arg(node.expr, ID=node.ID)
    type_map["call_arg_unpacked"] = lambda node: call_arg(node.expr, pack=pack_mode(node.pack))
    type_map["term_call"] = lambda node: node_types["term_call"](node.term, node.args if node.args else node_types["args"]())
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_func(input_types):
    node_types, type_map = regen_types(input_types)
    func = node_gen([Var("ID"), Var("args", type="func_arg", list=True), Var("return_type", type="type"), Var("block", type="block")], "func")
    node_types["func"] = func

    type_map["func"] = lambda node: func(node.ID, node.args, node.return_type.type if node.return_type else None, node.block)
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_class(input_types):
    node_types, type_map = regen_types(input_types)
    cls = node_gen([Var("ID"), Var("parent", type="type"), Var("block", type="block")], "class")
    node_types["class"] = cls

    type_map["class"] = lambda node: cls(node.ID, node.parent.type if node.parent else None, node.block)
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_math(input_types):
    node_types, type_map = regen_types(input_types)
    expr_affix = node_gen([Var("term", type="term"), Var("op"), Var("affix")], "expr_affix")
    node_types["expr_affix"] = expr_affix
    for node_type in "expr_prefix expr_postfix".split():
        del node_types[node_type]

    type_map["expr_prefix"] = lambda node: expr_affix(node.term, node.op, "prefix")
    type_map["expr_postfix"] = lambda node: expr_affix(node.term, node.op, "postfix")
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_bool(input_types):
    node_types, type_map = regen_types(input_types)
    expr_bool = node_gen([Var("expr1", type="expr"), Var("op"), Var("expr2", type="expr")], "expr_bool")
    node_types["expr_bool"] = expr_bool
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
    tuple = node_gen([Var("expr_list", type="expr", list=True)], "tuple")
    node_types["tuple"] = tuple
    tuple_expr = node_gen([Var("expr", type="expr")], "tuple_expr")
    node_types["tuple_expr"] = tuple_expr

    type_map["tuple"] = lambda node: tuple(node.expr_list) if len(node.expr_list) != 1 else tuple_expr(node.expr_list[0])
    type_map["tuple_trail"] = lambda node: tuple(node.expr_list)
    type_map["term_index"] = lambda node: node_types["term_index"](node.term, node.tuple if node.tuple else tuple())
    type_map["term_tuple"] = lambda node: node_types["term_tuple"](node.tuple if node.tuple else tuple())
    type_map["term_array"] = lambda node: node_types["term_array"](node.tuple if node.tuple else tuple())
    return node_types, map(leave=switch(type_map, key=lambda node: type(node).__name__))

def transform_block_chains(input_types):
    node_types, type_map = regen_types(input_types)
    if_chain = node_gen([Var("if_blocks", type="if_block", list=True), Var("else_block", type="block")], "if_chain")
    node_types["if_chain"] = if_chain
    try_chain = node_gen([Var("try_block", type="block"), Var("catch_blocks", type="catch_block", list=True), Var("finally_block", type="block")], "try_chain")
    node_types["try_chain"] = try_chain

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

def transform_tags(input_types):
    node_types, type_map = regen_types(input_types)
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
        if node.type == "string":
            node.value = codec(node.value[1:-1])[0]
        return node
    type_map = {}
    type_map["literal"] = map_literal
    return map(leave=switch(type_map, key=lambda node: type(node).__name__))

def map_op_prec(context):
    # UNARY FROM RIGHT
    # all from left

    # compares, in
    # slice
    # not
    # and
    # or
    # if a: b else c FROM RIGHT
    # assigns FROM RIGHT

    node_types = context.node_types
    op_types = "expr_math expr_compare expr_unary expr_in expr_not expr_bool".split()

    prec = [
        "%",
        "*/",
        "+-",
        "<< >>",
        "&",
        "^",
        "|",
    ]



    # layer_ops, node_type, assoc
    # assoc, op+type list
    def sort_ops(node):
        exprs, ops = list_terms(node)
        for layer in prec:
            layer_ops = layer.split()
            indices = [i for i, op in enumerate(ops) if op in layer_ops]
            matches = [node_types["expr_math"](exprs[index], ops[index], exprs[index + 1]) for index in indices]



    def list_terms(node):
        if type(node).__name__ not in math_types:
            return [node], []
        exprs1, ops1 = list_terms(node.expr1)
        exprs2, ops2 = list_terms(node.expr2)
        return exprs1 + exprs2, ops1 + [node.op] + ops2

    type_map = {}
    for type_name in math_types:
        type_map[type_name] = sort_ops
    return map(enter=switch(type_map, key=lambda node: type(node).__name__))

class Parser(ParserContext):
    def __init__(self):
        super().__init__(twocode_lexer(), twocode_grammar())
        node_types = self.node_types
        node_types, t_blocks = transform_blocks(node_types)
        node_types, t_args = transform_args(node_types)
        node_types, t_func = transform_func(node_types)
        node_types, t_class = transform_class(node_types)
        node_types, t_math = transform_math(node_types)
        node_types, t_bool = transform_bool(node_types)
        node_types, t_tuple = transform_tuple(node_types)
        node_types, t_block_chains = transform_block_chains(node_types)
        node_types, t_tags = transform_tags(node_types)
        node_types, t_repr = transform_repr(node_types)
        self.node_types = node_types
        m_literals = map_literals(self)
        #node_types, t_int = transform_int(node_types)
        #node_types, t_op_prec = transform_op_prec(node_types)

        def valid(ast):
            validate(ast)
            return ast

        self.validate = validate
        self.transforms += [
            t_blocks,
            t_args,
            t_func,
            t_class,
            t_math,
            t_bool,
            t_tuple,
            t_block_chains,
            t_tags,
            t_repr,
            m_literals,
            valid
        ]

# source paths + import command inside
# make it work interpreter-wise by following a __init__ script

class Twocode:
    def __init__(self):
        self.parser = Parser()
        self.parse = self.parser.parse
        self.node_types = self.parser.node_types

        add_context(self)

        from twocode.context.BuiltIns import gen_builtins
        self.builtins = gen_builtins(self)
        self.stack.insert(0, self.builtins)

        from twocode.context.BasicTypes import gen_types
        gen_types(self) # to builtins

        from twocode.context.Typing import gen_typing
        gen_typing(self)

        from twocode.context.NodeTypes import gen_node_types
        self.stack[-1].update(gen_node_types(self, self.node_types))
    def load(self, path):
        if os.path.isfile(path):
            ast = self.parser.parse(open(path, encoding="utf-8").read())
            self.eval(ast)

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
        obj = self.eval(code)
        if self.shell:
            if hasattr(obj, "__dict__"):
                if "__this__" in obj.__dict__ and obj.__dict__["__this__"] is None:
                    obj = None
                else:
                    obj = self.twocode.call(self.twocode.builtins.repr, ([obj], {}))
                    obj = self.twocode.unwrap_value(obj)
            if obj is not None:
                print(obj, file=sys.stderr, flush=True)
        return False
    def eval(self, code):
        ast = self.compile(code)
        # return ast
        return self.twocode.eval(ast)
    def exec(self, code):
        ast = self.compile(code)
        self.twocode.exec(ast)

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
    import Utils
    #Utils.root()

    console = Console()

    # console.twocode.log_mode().__enter__()
    #console.twocode.eval(console.twocode.load("code/data/Node.2c"))
    #console.twocode.eval(console.twocode.load("code/parser/Lexer.2c"))

    # console.twocode.eval(console.twocode.load("code/parser/Lexer.2c"))

    console.interact()
    #from languages.twocode.targets.Python import translate
    #print(translate(ast))










    # Enum

    # (name:String, pos:Int)
    ## affix tests
    # test this

# is block a stmt? if so remove chains

# translation post-translation is not validators is not grammar tests





# allow disabled printing

# the transform func is done at eval check, no validation access




# lvalues rvalues!!!!!

# return - only code block has to check really. but it does not just eval to last line

# delete empty statements - ;; -> ; if true ; false -> if true false

# class, A(B)

# add import statement and redo load API
# var f = Float, f = 3 breaks










# if true: { 0 }
# { 1 }


'''
todo:

code whitespace
indent parser


see visible exception, base
'''

# or specify pattern matching, tuples, catch
# casting, for loops, string interpolation
# macros and expr arguments, dynamic implementation

# translation language - apply __getattr__, __add__, __native__
# typing

# after that is playtime - redo this in the language. compile it in rust
# then we can try optimized shader/whatnot, and release it, or start redoing haxe code

'''
func f(n): return n*n
    func has no mul LUL
'''

# indent, tests, ws, string format




# is there a default post-loader?

# push all constructor code into the constructor, making the fields load nothing


# a func inside a class has this inserted into it and is accessible as Class.func(this, *args. **kwargs)
# @static removes that


# typing, export






# func - convert to this
#  @static
# enforce not this on operators








    # haxe forces writing in static
    # python does not do that, module functions
    # current - ?

    # Int2.floor
    # math.vectors.floor

    # module.path.a
    # import x as y
    # __init__ that fully builds public interface, and we write in core.py
    # __imports__ as in haxe
    # place-independent code

    # public:
    # only classes, no module-level anything
    # no static vars, yes static funcs, need exclusive names
    # @context - creates a current, pass/forward=False\

# this in functions
# make them printable, classes as well
#
# test for sensible basic operations
# that class' fields (meta) have correct types


# native signature
# explicit types

        # __static__ - doesnt start with this, dont inherit
        # __vars__ - a list of macros - type, default
        # __tags__ - dict()

        # by value/ref? nullable?

        # __dict__ a scope of the object's fields
        # __slots__ - for when you want to disable this and list them by name, no longer has __dict__ then
        # mappingproxy - just a read-only dict that enforces string keys
            # setattr to class works



# 0.__add__






# precedence,


# var f = func(x,y): return (x + y) / 2
# also 3/2 not working

# AttributeError: 'dict' object has no attribute '__bound__'

# require empty line after indent

















# why does Int() return {}
# that closure scope is accessible Var











# class func print, native prints, basics print
#, printing
# printing - funcs, classes, objects (a b)
# make a func repr work - needs context and unwrap value








# dict literal, set literal









# list comprehension

# +=
# mutual
# int div
