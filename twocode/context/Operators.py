op_math = {
    "+": "__add__",
    "-": "__sub__",
    "*": "__mul__",
    "/": "__div__",
    "%": "__mod__",
    "&": "__and__",
    "|": "__or__",
    "^": "__xor__",
    "<<": "__lshift__",
    ">>": "__rshift__",
}
op_compare = {
    "<": "__lt__",
    ">": "__gt__",
    "<=": "__le__",
    ">=": "__ge__",
    "!=": "__ne__",
    "==": "__eq__",
}
op_unary = {
    "+": "__pos__",
    "-": "__neg__",
    "~": "__invert__",
}
op_assign = {
    "=": "__mov__",
    "+=": "__iadd__",
    "-=": "__isub__",
    "*=": "__imul__",
    "/=": "__idiv__",
    "%=": "__imod__",
    "&=": "__iand__",
    "|=": "__ior__",
    "^=": "__ixor__",
    "<<=": "__ilshift__",
    ">>=": "__irshift__",
}
def increment(obj):
    obj.__this__ += 1
def decrement(obj):
    obj.__this__ -= 1