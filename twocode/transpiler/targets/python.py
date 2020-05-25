import textwrap
import os
from twocode.utils.node import switch

delim = " " * 4

map = {
    "code": lambda node: "\n".join(py_code(stmt) for stmt in node.lines),
    "decl": lambda node: node.id,
    "call_arg": lambda node: pack_args(node.pack) + ("{}=".format(node.id) if node.id else "") + py_code(node.value),
    "for_loop": lambda node: "for " +\
        (", ".join(py_code(name) for name in node.names.names) if type(node.names).__name__ == "multiple_id_tuple" and len(node.names.names) > 1 else py_code(node.names)) +\
        " in {}:".format(py_code(node.expr)) + wrap_block(node.block),
    "multiple_id": lambda node: node.id,
    "multiple_id_tuple": lambda node: "(" + ", ".join(py_code(name) for name in node.names) + ("" if len(node.names) > 1 else ",") + ")",
    "multiple_term": lambda node: py_code(node.term),
    "multiple_term_tuple": lambda node: "(" + ", ".join(py_code(term) for term in node.terms) + ("" if len(node.terms) > 1 else ",") + ")",
    "multiple_decl": lambda node: py_code(node.decl),
    "multiple_decl_tuple": lambda node: "(" + ", ".join(py_code(decl) for decl in node.declares) + ("" if len(node.declares) > 1 else ",") + ")",
    "stmt_tuple": "{tuple}",
    "stmt_assign": lambda node: \
        (", ".join(py_code(term) for term in node.terms.terms) if type(node.terms).__name__ == "multiple_term_tuple" and len(node.terms.terms) > 1 else py_code(node.terms)) +\
        " " + " ".join(py_code(assign) for assign in node.assign_chain),
    "stmt_var": lambda node: \
        (", ".join(py_code(decl) for decl in node.declares.declares) if type(node.declares).__name__ == "multiple_decl_tuple" and len(node.declares.declares) > 1 else py_code(node.declares)) +\
        (" " + " ".join(py_code(assign) for assign in node.assign_chain) if node.assign_chain else ""),
    "stmt_return": lambda node: "return" + (" " + py_code(node.tuple) if node.tuple else ""),
    "stmt_break": "break",
    "stmt_continue": "continue",
    "assign": "{op} {tuple}",
    "tuple_expr": "{expr}",
    "tuple": lambda node: ", ".join(py_code(expr) for expr in node.expr_list) + ("," if len(node.expr_list) == 1 else ""),
    "args": lambda node: ", ".join(py_code(arg) for arg in node.args),
    "expr_term": "{term}",
    "expr_math": "{expr1} {op} {expr2}",
    "expr_compare": "{expr1} {op} {expr2}",
    "expr_unary": "{op}{expr}",
    "expr_affix": lambda node: node.op + py_code(node.term) if node.affix == "prefix" else py_code(node.term) + node.op, # CANT
    "expr_if": "{if_chain}",
    "expr_for": "{for_loop}",
    "expr_while": "{while_loop}",
    "expr_try": "{try_chain}",
    "term_id": lambda node: node.id if node.id != "this" else "self",
    "term_attr": "{term}.{id}",
    "term_key": "{term}[{tuple}]",
    "term_literal": "{literal}",
    "term_list": "[{tuple}]",
    "term_map": "{{{map}}}",
}

def map_term_call(node):
    term = py_code(node.term)
    args = py_code(node.args)
    if term == "native":
        return eval(args)
    return "{}({})".format(term, args)
map["term_call"] = map_term_call
def map_if_chain(node):
    buf = []
    buf.append("if {}:".format(py_code(node.if_blocks[0].expr)))
    buf.append(wrap_block(node.if_blocks[0].block))
    for else_if_block in node.if_blocks[1:]:
        buf += [
            "\n",
            "else if {}:".format(py_code(else_if_block.expr)),
            wrap_block(else_if_block.block),
        ]
    if node.else_block:
        buf += [
            "\n",
            "else:",
            wrap_block(node.else_block),
        ]
    return "".join(buf)
map["if_chain"] = map_if_chain
literal_map = {
    "null": lambda value: "None",
    "boolean": lambda value: "True" if value else "False",
    "integer": lambda value: str(value),
    "float": lambda value: str(value),
    "string": lambda value: repr(value),
}
map["literal"] = lambda node: literal_map[node.type](node.value)

def wrap_block(node):
    lines = py_code(node).splitlines()
    if not lines:
        return "\n" + delim + "pass"
    return "".join("\n" + delim + line for line in lines)
def pack_args(mode):
    if not mode:
        return ""
    if mode == "args":
        return "*"
    if mode == "kwargs":
        return "**"

def gen_py_code_func(type_name):
    format = map.get(type_name)
    if isinstance(format, str):
        return lambda node: format.format(**{var.name: py_code(node.__dict__[var.name]) for var in type(node).vars})
    if callable(format):
        return format
code_map = {type_name: gen_py_code_func(type_name) for type_name in map}
py_code = switch(code_map, key=lambda node: type(node).__name__)

def gen_source():
    from .. import import_code_env
    import_code_env()

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
                # do this only if it's a complex expr? eg not if a direct literal
                # do it if it's a term
        return default_lines
    def py_func(f, cls=None, name=None):
        args = [arg.name + ("=None" if arg.default_ else "") for arg in f.args]
        if cls and c.bound(f, cls):
            args[0] = "self"
        block = c.parser.node_types["code"](func_defaults(f) + f.code.lines)
        return "def {}({}):{}".format(
            name,
            ", ".join(args),
            wrap_block(block)
        )

    def py_class(cls):
        qualname = op.qualname(cls).split(".")[-1]

        attrs = []
        attr_lines = []
        for name, field in sorted(cls.__fields__.items()):
            if field.__type__ is Attr:
                attrs.append(name)
                var_stmt = c.parse("this.id = null").lines[0]
                var_stmt.terms.term.id = name
                if field.default_:
                    var_stmt.assign_chain[0].tuple = field.default_
                attr_lines.append(var_stmt)

        funcs = {}
        for name, field in sorted(cls.__fields__.items()):
            if field.__type__ is Func:
                funcs[name] = field
                if c.bound(field, cls):
                    def transform(node):
                        type_name = type(node).__name__
                        if type_name == "term_id" and node.id == attr:
                            new_node = c.parse("this.{}".format(attr))
                            new_node = new_node.lines[0].tuple.expr.term # or parse what?
                            transp.node_to_scope[new_node] = transp.node_to_scope[node]
                            transp.node_to_scope[new_node.term] = transp.node_to_scope[node]
                            # for all subnodes
                            return new_node
                        return node
                    for attr in attrs:
                        field.code = transp.code_edit.map_name(field.code, attr, transform, transp.type_to_scope[cls])
                        # don't regenerate it 40 times for Game
                        # also it better iterate

        py_init = c.obj.Func()
        py_init.code = c.parser.node_types["code"](attr_lines)
        init = funcs.pop("__init__", None)
        if init:
            py_init.code.lines.extend(init.code.lines)
            py_init.args = init.args
        else:
            py_init.args = [c.obj.Arg("this", cls)]

        lines = []
        lines.append("class {}:".format(qualname))
        if py_init.args[1:] or py_init.code.lines:
            lines.append(
                textwrap.indent(py_func(py_init, cls, "__init__"), delim)
                    # do this more often, in repr, in state parser
            )
        func_lines = []
        for name, func in sorted(funcs.items()): # odict
            if func.__type__ is Func:
                func_lines.append(
                    textwrap.indent(py_func(func, cls, name), delim)
                )
        if func_lines:
            lines.append("")
            lines.extend(func_lines)

        return "\n".join(lines)

    # NOTE: create modules
    def search_module(module):
        if module.__type__ is not Env:
            info = ModuleInfo()
            info.obj = module
            info.path = uw(module.__path__)
            modules.append(info)

        for name in sorted(module.__this__):
            obj = module.__this__[name].value
            if obj.__type__ is Module:
                search_module(obj)
    modules = []
    search_module(transp.env)

    # NOTE: put classes into modules
    for cls in transp.all_classes:
        path = op.qualname(cls).split(".")
        module_path = ".".join(path[:-1])
        module = next(module for module in modules if module.path == module_path)
        code = py_class(cls)
        module.classes.append(code)
        module.names.add(path[-1])

    # NOTE: put imports into modules
    context_builtins = call(transp.env, "builtins").values()
    for module in modules:
        for name in sorted(module.obj.__this__):
            obj = module.obj.__this__[name].value
            if obj.__type__ is Class and obj not in context_builtins:
                if name in module.names:
                    continue
                path = op.qualname(obj).split(".")
                module.imports.append("from {} import {}{}".format(
                    ".".join(path[:-1]), #
                    path[-1],
                    "" if path[-1] == name else " as {}".format(name),
                ))
                module.names.add(name)

    # NOTE: create files
    transp.files = {}
    transp.files["__init__.py"] = ""
    for module in modules:
        if not module.classes:
            continue
        path = module.path.split(".")
        file = os.path.sep.join(path) + ".py"
        transp.files[file] = str(module)

        for i in range(1, len(path)):
            package_file = os.path.sep.join(path[:i] + ["__init__.py"])
            transp.files[package_file] = ""

    return
    entry = "Game.ABC"
    cls = next(cls for cls in transp.all_classes if op.qualname(cls) == entry)
    module = next(module for module in modules if module.path == entry)
    module.main = textwrap.dedent("""
        {} = {}()
        {}.main()
    """.format(entry.lower(), entry, entry.lower())).strip()

def run():
    pass
    # run as a process
    # python ABC.py

class ModuleInfo: #
    def __init__(self):
        self.obj = None
        self.path = None
        self.classes = []
        self.imports = [] # depend, includes (native?) SORT
        self.names = set()
        self.main = None
        # import at the end if circular
        # set static attrs after
    def __str__(self):
        parts = []
        if self.imports:
            parts.append("\n".join(self.imports))
        parts.append("")
        parts.append("\n\n".join(self.classes))
        if self.main:
            parts.append(textwrap.dedent("""
                if __name__ == "__main__":
                    {}
            """).strip()).format(textwrap.indent(self.main, delim))
            parts.append("")
        return "\n".join(parts) + "\n"























# remove the "this" hack, new approach:
# like all languages, we abuse the flexibility of the node types

# so, we store everything we might want to analyze (e.g. is a func bound?(no longer with this->self), is a node typed? (self no longer means this, can't be resolved))
# and then apply a sequence of destructive filters

# replace:
# == None -> is None





# unwrapping complex expr:
# if part of the expr is a statement, extract it a statement before, save into a temporary var
# then pass the thing

# e.g.

# return pos++
# ->
# tmp = pos
# pos += 1
# return tmp

# return ++pos
# ->
# pos += 1
# return pos


# g(f().x++)
# ->
# tmp = f()
# tmp2 = tmp.x
# tmp.x += 1
# g(tmp2)

# g(o.x++)
# ->
# tmp = o.x
# o.x += 1
# g(tmp)

# if i know it's an int:
# o.x += 1
# g(o.x - 1)

# some of these depend on whether the term has side effects
# has_side_effects?
# -> .pure
# .lvalue

# such an analyzer is able to give you  these answers about certain constructs
# it's also possible to cache these -> analyze the entire program, then do [obj].pure


# remove initialization line if the attr is assigned to from a const (without reading it first)
            # include possible use of other methods to figure out that



# a func that breaks apart a module tree to set it to 1 class per module
# it will need to analyze all references etc

