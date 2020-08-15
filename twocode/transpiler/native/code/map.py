from twocode.transpiler.native.code import node_types as t

native_map = {
    'code': lambda node: t.Code([map(stmt) for stmt in node.lines]),
    'stmt_tuple': lambda node: t.StmtTuple(map(node.tuple)),
    'tuple_expr': lambda node: t.TupleExpr(map(node.expr)),
    'expr_class': lambda node: t.ExprClass(map(node.class_def)),
    'class_def': lambda node: t.ClassDef(node.id, map(node.base), node.block), # todo: node.fields
}


def map(node):
    if node is None:
        return None
    # todo: isn't getting type of every node slow?
    type_name = type(node).__name__
    if type_name in native_map:
        return native_map[type_name](node)
    print('NOT FOUND IN NATIVE CODE MAPPING', type_name)
