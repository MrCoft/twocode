from twocode.transpiler.native.code import node_types as t

source_map = {
    t.Code: lambda node: '\n'.join(map(stmt) for stmt in node.lines),
    t.StmtTuple: lambda node: map(node.tuple),
    t.TupleExpr: lambda node: map(node.expr),
    t.ExprClass: lambda node: map(node.class_def),
    t.ClassDef: lambda node: f'class {node.id}:{wrap_block(map(node.fields))}', # todo: some inline magic
}


def wrap_block(node, start_block=True, expand: bool=False):
    margin = lambda: " " if start_block else ""
    lines = map(node).splitlines()
    if not lines:
        return margin() + "pass"
    if len(lines) > 1 or expand:
        return "".join("\n" + " " * 4 + line for line in lines)
    else:
        return margin() + lines[0]


def map(node):
    if node is None:
        return ''
    # todo: maybe eventually override to_string, not now
    node_type = type(node)
    if node_type in source_map:
        return source_map[node_type](node)
    print('NOT FOUND IN SOURCE MAPPING', node_type.__name__)
