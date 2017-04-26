map_format = {
    "type_ID": "{ID}",
    "type_params": "{ID}<{params}>",
    "stmt_tuple": "{tuple}",
    "stmt_break": "break",
    "stmt_continue": "continue",
    "assignment": "{op} {tuple}",
    "tuple_expr": "{expr}",
    "expr_term": "{term}",
    "expr_math": "{expr1} {op} {expr2}",
    "expr_compare": "{expr1} {op} {expr2}",
    "expr_unary": "{op}{term}",
    "expr_bool": "{expr1} {op} {expr2}",
    "expr_in": "{expr1} in {expr2}",
    "expr_if": "{if_chain}",
    "expr_try": "{try_chain}",
    "expr_for": "{for_loop}",
    "expr_while": "{while_loop}",
    "expr_func": "{func}",
    "expr_class": "{class}",
    "term_ID": "{ID}",
    "term_access": "{term}.{ID}",
    "term_index": "{term}[{tuple}]",
    "term_literal": "{literal}",
    "term_call": "{term}({args})",
    "term_tuple": "({tuple})",
    "term_array": "[{tuple}]",
    "literal": "{value}",
}
map_lambda = {
    "code": lambda node: "\n".join(str(stmt) for stmt in node.lines),
    "type_func": lambda node: "{}->{}".format(",".join(str(type) for type in node.arg_types), ",".join(str(type) for type in node.return_types)),
    "type_tuple": lambda node: "({})".format(",".join(str(type) for type in node.types)),
    "class": lambda node: "class" + (" " + node.ID if node.ID else "") + ":" + wrap_block(node.block),
    "func": lambda node: "func" + (" " + node.ID if node.ID else "") + "({})".format(", ".join(str(arg) for arg in node.args)) + ("->{}".format(node.return_type) if node.return_type else "") + ":" + wrap_block(node.block),
    "func_arg": lambda node: pack_args(node.pack) + node.ID + (":{}".format(str(node.type)) if node.type else "") + (" = {}".format(str(node.value)) if node.value else ""),
    "call_arg": lambda node: pack_args(node.pack) + ("{}=".format(str(node.ID)) if node.ID else "") + str(node.value),
    "decl": lambda node: str(node.ID) + (":{}".format(str(node.type.type)) if node.type else ""),
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
}
def map_if_chain(node):
    code = ""
    code += "if {}:".format(str(node.if_blocks[0].cond))
    if len(node.if_blocks) == 1 and node.else_block is None:
        code += wrap_block(node.if_blocks[0].block)
        return code
    else:
        code += wrap_block(node.if_blocks[0].block, expand=True)
        for else_if_block in node.if_blocks[1:]:
            code += "\n"
            code += "else if {}:".format(str(else_if_block.cond))
            code += wrap_block(else_if_block.block, expand=True)
        if node.else_block:
            code += "\n"
            code += "else:"
            code += wrap_block(node.else_block, expand=True)
        return code
map_lambda["if_chain"] = map_if_chain

def wrap_block(node, start_block=True, expand=False):
    margin = lambda: " " if start_block else ""
    lines = str(node).splitlines()
    if not lines:
        return margin() + "{}"
    if len(lines) > 1 or expand:
        return "\n".join("\n" + " " * 4 + line for line in lines)
    else:
        return margin() + "{{ {} }}".format(lines[0])

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