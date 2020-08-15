# todo: node base class had its reasons


class Code:
    def __init__(self, lines=None):
        if lines is None: lines = []
        self.lines = lines


# noinspection PyShadowingBuiltins
class StmtTuple:
    # TODO: skip this node
    def __init__(self, tuple):
        self.tuple = tuple


class TupleExpr:
    def __init__(self, expr):
        self.expr = expr


class ExprClass:
    # TODO: skip this node
    def __init__(self, class_def):
        self.class_def = class_def


class ClassDef:
    # TODO: why does 2c do "block"? that's dangerous
    def __init__(self, id=None, base=None, fields=None):
        if fields is None: fields = []
        self.id = id
        self.base = base
        self.fields = fields
