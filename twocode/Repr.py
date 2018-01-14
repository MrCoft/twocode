import twocode.utils.String

map_format = {
    "type_id": "{id}",
    "type_params": "{id}<{params}>",
    "decl": "{id}{type}",
    "decl_type": ":{type}",
    "range": "{min}...{max}",
    "stmt_tuple": "{tuple}",
    "stmt_break": "break",
    "stmt_continue": "continue",
    "stmt_import": "{imp}",
    "assignment": "{op} {tuple}",
    "tuple_expr": "{expr}",
    "expr_term": "{term}",
    "expr_math": "{expr1} {op} {expr2}",
    "expr_compare": "{expr1} {op} {expr2}",
    "expr_unary": "{op}{expr}",
    "expr_bool": "{expr1} {op} {expr2}",
    "expr_in": "{expr1} in {expr2}",
    "expr_if": "{if_chain}",
    "expr_try": "{try_chain}",
    "expr_for": "{for_loop}",
    "expr_while": "{while_loop}",
    "expr_in_block": "{in_block}",
    "expr_func": "{func_def}",
    "expr_class": "{class_def}",
    "expr_range": "{range}",
    "expr_ellipsis": "...",
    "expr_decorator": "@{term} {expr}",
    "expr_macro": "macro {code}",
    "term_id": "{id}",
    "term_attr": "{term}.{id}",
    "term_key": "{term}[{tuple}]",
    "term_literal": "{literal}",
    "term_call": "{term}({args})",
    "term_tuple": "({tuple})",
    "term_list": "[{tuple}]",
    "term_map": "[{map}]",
}
map_lambda = {
    "code": lambda node: "\n".join(str(stmt) for stmt in node.lines),
    "imp": lambda node: ("from {} ".format(".".join(node.module)) if node.module else "") + "import " + ", ".join(".".join(path.path) + (" as {}".format(path.name) if path.name else "") for path in node.imports),
    "type_func": lambda node: "{}->{}".format(",".join(str(type) for type in node.arg_types), ",".join(str(type) for type in node.return_types)),
    "type_tuple": lambda node: "({})".format(",".join(str(type) for type in node.types)),
    "class_def": lambda node: "class" + (" " + node.id if node.id else "") + ("({})".format(str(node.base)) if node.base else "") + ":" + wrap_block(node.block),
    "call_arg": lambda node: pack_args(node.pack) + ("{}=".format(str(node.id)) if node.id else "") + str(node.value),
    "in_block": lambda node: "in {}:".format(str(node.expr)) + wrap_block(node.block),
    "for_loop": lambda node: "for {} in {}:".format(str(node.var), str(node.iter)) + wrap_block(node.block),
    "while_loop": lambda node: "while {}:".format(str(node.cond)) + wrap_block(node.block),
    "stmt_assign": lambda node: str(node.tuple) + " " + "".join(str(assign) for assign in node.assign_chain),
    "stmt_var": lambda node: "var {}".format(", ".join(str(decl) for decl in node.vars)) + " " + "".join(str(assign) for assign in node.assign_chain),
    "stmt_return": lambda node: "return" + (" " + str(node.tuple) if node.tuple else ""),
    "tuple": lambda node: ", ".join(str(expr) for expr in node.expr_list) + ("," if len(node.expr_list) == 1 else ""),
    "args": lambda node: ", ".join(str(arg) for arg in node.args),
    "expr_affix": lambda node: node.op + str(node.term) if node.affix == "prefix" else str(node.term) + node.op,
    "expr_not": lambda node: "not " + str(node.expr) if not type(node.expr).__name__ == "expr_in" else "{} not in {}".format(str(node.expr.expr1), str(node.expr.expr2)),
    "expr_block": lambda node: wrap_block(node.block, start_block=False),
    "map": lambda node: ", ".join("{}: {}".format(item.key, item.value) for item in node.item_list),
    "literal": lambda node: node.value if not node.type == "string" else twocode.utils.String.escape(node.value),
}

def map_func_def(node):
    buf = []
    block = str(node.block)
    arrow = block.startswith("return ") and "\n" not in block and not node.id and not node.return_type
    if arrow:
        args_code = None
        if len(node.args) == 1:
            arg = node.args[0]
            if not (arg.pack or arg.default or arg.macro or arg.type):
                args_code = arg.id
        if not args_code:
            args_code = "({})".format(", ".join(str(arg) for arg in node.args))
        buf += [
            args_code,
            "->",
            block[len("return "):],
        ]
    else:
        block_code = wrap_block(block)
        buf += [
            "func",
            " " + node.id if node.id else "",
            "({})".format(", ".join(str(arg) for arg in node.args)),
            "->{}".format(node.return_type) if node.return_type else "",
            ":" + block_code,
        ]
    return "".join(buf)
map_lambda["func_def"] = map_func_def
# REASON:
# easy implementation, but a correct solution would travel the graph
# in a 4-step sequence of ifs and type checks, effectively the same
# as stringing it
def map_func_arg(node):
    buf = []
    buf.append(pack_args(node.pack))
    default = str(node.default) if node.default else ""
    opt = default == "null"
    if opt:
        buf.append("?")
    buf += [
        "macro " if node.macro else "",
        node.id,
        ":{}".format(str(node.type)) if node.type else "",
    ]
    if not opt:
        buf.append("={}".format(default) if default else "")
    return "".join(buf)
map_lambda["func_arg"] = map_func_arg
def map_if_chain(node):
    buf = []
    buf.append("if {}:".format(str(node.if_blocks[0].cond)))
    if len(node.if_blocks) == 1 and node.else_block is None:
        buf.append(wrap_block(node.if_blocks[0].block))
        return "".join(buf)
    else:
        buf.append(wrap_block(node.if_blocks[0].block, expand=True))
        for else_if_block in node.if_blocks[1:]:
            buf += [
                "\n",
                "else if {}:".format(str(else_if_block.cond)),
                wrap_block(else_if_block.block, expand=True),
            ]
        if node.else_block:
            buf += [
                "\n",
                "else:",
                wrap_block(node.else_block, expand=True),
            ]
        return "".join(buf)
map_lambda["if_chain"] = map_if_chain

# allow if chain directly?

# make that disappear -  a func jumps that in its mapping yet a class has to do it so weirdly?
# rework class to use a transplant while we're at it
# or support the multiple vars decl
# eval None is None right?

# type_params


def wrap_block(node, start_block=True, expand=False):
    margin = lambda: " " if start_block else ""
    lines = str(node).splitlines()
    if not lines:
        return margin() + "{}"
    if len(lines) > 1 or expand:
        return "".join("\n" + " " * 4 + line for line in lines)
    else:
        return margin() + lines[0]

def pack_args(mode):
    if not mode:
        return ""
    if mode == "args":
        return "*"
    if mode == "kwargs":
        return "**"
# limit chars per line
def gen_repr(node_type):
    type_name = node_type.__name__
    if type_name in map_format:
        msg = map_format[type_name]
        vars = [var.name for var in node_type.vars]
        return lambda node: msg.format(**{var: str(node.__dict__[var]) for var in vars})
    if type_name in map_lambda:
        return map_lambda[type_name]
