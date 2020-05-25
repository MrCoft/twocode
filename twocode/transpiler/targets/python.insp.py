map_format = {
    "stmt_tuple": "{tuple}",
    "stmt_break": "break",
    "stmt_continue": "continue",
    "assign": "{op} {tuple}",
    "tuple_expr": "{expr}",
    "expr_term": "{term}",
    "expr_math": "{expr1} {op} {expr2}",
    "expr_compare": "{expr1} {op} {expr2}",
    "expr_unary": "{op}{expr}",
    "expr_if": "{if_chain}",
    "expr_try": "{try_chain}",
    "expr_for": "{for_loop}",
    "expr_while": "{while_loop}",
    "term_id": "{id}",
    "term_attr": "{term}.{id}",
    "term_key": "{term}[{tuple}]",
    "term_literal": "{literal}",
    "term_list": "[{tuple}]",
    "term_map": "{{{map}}}",
}
map_lambda = {
    "code": lambda node: "\n".join(py_repr(stmt) for stmt in node.lines),
    "decl": lambda node: node.id,
    "stmt_assign": lambda node: py_repr(node.terms.term) + " " + py_repr(node.assign_chain[0]),
    "stmt_var": lambda node: "var" + py_repr(node.declares.decl) + " " + py_repr(node.assign_chain[0]),
    "stmt_return": lambda node: "return" + (" " + py_repr(node.tuple) if node.tuple else ""),
    "literal": lambda node: node.value if not node.type == "string" else repr(node.value),
}

def wrap_block(node):
    lines = py_repr(node).splitlines()
    if not lines:
        return " pass"
    return "".join("\n" + " " * 4 + line for line in lines)

def map_term_call(node):
    term = py_repr(node.term)
    args = py_repr(node.args)
    if term == "native":
        return eval(args)
    return "{}({})".format(term, args)
map_lambda["term_call"] = map_term_call

def py_repr(node):
    node_type = __builtins__.type(node)
    type_name = node_type.__name__
    if type_name in map_format:
        msg = map_format[type_name]
        vars = [var.name for var in node_type.vars]
        return msg.format(**{var: str(node.__dict__[var]) for var in vars})
    if type_name in map_lambda:
        return map_lambda[type_name](node)
    raise Exception("can't map {} node".format(type_name))
    return repr(node)

def func_defaults(f):
    default_lines = []
    for arg in f.args:
        if arg.default_:
            default_stmt = c.parse("if id == null: { id = val }").lines[0]
            if_block = default_stmt.tuple.expr.if_chain.if_blocks[0]
            if_block.expr.expr1.term.id = arg.name
            if_block.block.lines[0].terms.term.id = arg.name
            if_block.block.lines[0].assign_chain[0].tuple.expr = arg.default_
            default_lines.append(default_stmt)
    return default_lines

def py_func(f, name=None):
    args = [arg.name for arg in f.args]
    block = c.parser.node_types["code"]()
    block.lines = func_defaults(f) + f.code.lines
    return "def {}({}):{}".format(
        name,
        ", ".join(args),
        wrap_block(block)
    )

#f = c.eval(c.parse('func f(a, b=2): return "xo"'))
#print(py_func(f))

def py_class(cls):
    path = "_".join(op.qualname(cls).split("."))
    vars = {}

    var_lines = []
    attrs = [name for name, field in cls.__fields__.items() if field.__type__ is Attr]
    for name, field in cls.__fields__.items():
        if field.__type__ is Attr:
            var_stmt = c.parse("this.id = null").lines[0]
            var_stmt.terms.term.id = name
            if field.default_:
                var_stmt.assign_chain[0].tuple = field.default_
            var_lines.append(var_stmt)

        if field.__type__ is Func:
            if c.bound(field, cls):
                def transform(node):
                    type_name = __builtins__.type(node).__name__
                    if type_name == "term_id" and node.id == attr:
                        new_node = c.parse("this.{}".format(attr))
                        new_node = new_node.lines[0].tuple.expr.term # or parse what?
                        node_to_scope[new_node] = node_to_scope[node]
                        node_to_scope[new_node.term] = node_to_scope[node]
                        # for all subnodes
                        return new_node
                    return node
                for attr in attrs:
                    field.code = map_name(field.code, attr, transform)
                print(py_func(field))



                # bind "this" variables
                # proper solution:
                # in that case, find all instances of where THAT NAME is mentioned
                    # test that? shadowing?

    init_code = c.parser.node_types["code"]()
    init_code_lines = var_lines
    if "__init__" in cls.__fields__:
        init_code_lines.extend(cls.__fields__["__init__"].code.lines)
    py_init = c.obj.Func()
    # py_init.args = init.args[1:]
    py_init.code = init_code

    # boundmethod printing

    # remove init, modify it to add lines

    return None

    return "var {} = {}".format(path, py_func(py_init))

cls_code = textwrap.dedent("""
    class V:
        var x:Int = 2
        var y:Int

        func __init__(_y=5):
            y = _y
        func sum():
            return x + y
""").strip()
V = c.eval(c.parse(cls_code))
# print(py_class(V))
for type in all_types:
    print(py_class(type))

result = """
    class V:
        def __init__(self, _y=5):
            self.x = 2
            self.y = None
            self.y = _y
        def sum(self):
            return x + y
""" # back into parse?

# missing: if chain