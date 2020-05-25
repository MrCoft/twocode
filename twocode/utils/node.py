from twocode import utils
import twocode.utils.code
import functools
import builtins
import twocode.utils.string
import copy

DELIM = ".\t".replace("\t", " " * (4 - 1))

class Node:
    def __init__(self, **kwargs):
        self.children = []
        self.parents = []
        self.__dict__.update(kwargs)
    def __repr__(self):
        lines = [
            "{}: {}".format(key, value) for key, value in sorted(utils.redict(self.__dict__, "children parents".split()).items())
        ]
        for child in self.children:
            for line in str(child).splitlines():
                lines.append(DELIM + line)
        return "\n".join(lines)
    def __eq__(self, other):
        if utils.redict(self.__dict__, "children parents".split()) != utils.redict(other.__dict__, "children parents".split()):
            return False
        return self.children == other.children
    def __copy__(self):
        return Node(children=self.children.copy(), **utils.redict(self.__dict__, "children parents".split()))
    def __deepcopy__(self, memo):
        return Node(children=[copy.deepcopy(child, memo=memo) for child in self.children], **utils.redict(self.__dict__, "children parents".split())) # deep

def map(enter=None, leave=None):
    def filter(node):
        if enter:
            node = enter(node)
        node.children = [filter(child) for child in node.children]
        if leave:
            node = leave(node)
        return node
    return filter

def switch(map, key):
    def filter(node):
        val = key(node)
        if val in map:
            node = map[val](node)
        return node
    return filter

def fold(f, iter_func):
    def filter(node):
        return f(node, [filter(child) for child in iter_func(node)])
    return filter
fold_children = lambda f: fold(f, lambda node: node.children)
fold_parents = lambda f: fold(f, lambda node: node.parents)
fold_parents_loops = lambda f: fold(f, lambda node: [parent for parent in node.parents if parent is not node])

def range_call(f):
    def filter(node, *, pos=0):
        if node.children:
            children, length = [], 0
            for child in node.children:
                child, l = filter(child, pos=pos+length)
                children.append(child)
                length += l
            node.children = children
        else:
            length = 1
        return f(node, (pos, length)), length
    return filter

def l(f):
    @functools.wraps(f)
    def wrapped(node, *args, **kwargs):
        result = f(node, *args, **kwargs)
        return result if result else node
    return wrapped

class Var:
    def __init__(self, name, type=None, list=False):
        self.name = name
        self.type = type
        self.list = list
def node_gen(name, vars):
    class GenNode:
        def __init__(self, *args, **kwargs):
            self.__dict__ = {var.name: None if not var.list else [] for var in GenNode.vars}
            for var, arg in zip(GenNode.vars, args):
                self.__dict__[var.name] = arg
            self.__dict__.update(kwargs)
        @property
        def children(self):
            children = []
            for var in GenNode.vars:
                if var.type and self.__dict__[var.name]:
                    if not var.list:
                        children.append(self.__dict__[var.name])
                    else:
                        children.extend(self.__dict__[var.name])
            return children
        @children.setter
        def children(self, children):
            children = iter(children)
            for var in GenNode.vars:
                if var.type and self.__dict__[var.name]:
                    if not var.list:
                        self.__dict__[var.name] = next(children)
                    else:
                        list_var = self.__dict__[var.name]
                        for i in range(len(list_var)):
                            list_var[i] = next(children)
        def __repr__(self):
            return self.str_func()
        def str_func(self, *, delim=None, str=str):
            if delim is None: delim = DELIM
            name = GenNode.name_func(self)
            items = GenNode.attr_lines(self, delim=delim, str=str)
            if not items:
                return name
            elif len(items) == 1:
                # NOTE: the reason this does not use compact_node
                value = next(iter(self.__dict__.values()))
                if hasattr(value, "children"):
                    return name + " " + items[0]
                else:
                    return name + ":" + items[0]
            else:
                lines = [name + ":"]
                for item in items:
                    for line in item.splitlines():
                        lines.append(delim + line)
                return "\n".join(lines)
        @staticmethod
        def name_func(node):
            return type(node).__name__
        @staticmethod
        def attr_lines(node, *, delim=None, str=str):
            if delim is None: delim = DELIM
            if len(node.__dict__) == 1:
                value = next(iter(node.__dict__.values()))
                if hasattr(value, "children"):
                    return [str(value)]
                else:
                    # REASON: to have ":" before str(value), and to do lists of all sizes the same way
                    return [compact_block(value, delim=delim, str=str)]
            format_value = lambda value: compact_block(value, delim=delim, str=str)
            arg_vars = [var.name for var in type(node).vars]
            return [
                "{}:{}".format(key, format_value(value)) for key, value in sorted(utils.redict(node.__dict__, arg_vars).items())
            ] + [
                "{}:{}".format(key, format_value(node.__dict__[key])) for key in arg_vars
            ]
        def __copy__(self):
            return GenNode(**{var.name: self.__dict__[var.name] for var in GenNode.vars})
        def __deepcopy__(self, memo):
            return GenNode(**{var.name: copy.deepcopy(self.__dict__[var.name], memo=memo) for var in GenNode.vars})

    GenNode.vars = vars
    GenNode.__name__ = name
    return GenNode

def compact_value(value, *, str=str):
    if type(value) is builtins.str:
        return twocode.utils.string.escape(value)
    elif type(value) is list:
        if value:
            return "\n".join(str(item) for item in value)
        else:
            return "[]"
    else:
        return str(value)
def compact_branches(value, *, delim=None, str=str):
    if delim is None: delim = DELIM
    if type(value) is builtins.str:
        return False
    if type(value) is list:
        return bool(value)
    lines = str(value).splitlines()
    return len([line for line in lines if not line.startswith(delim)]) > 1
def compact_block(value, *, delim=None, str=str):
    if delim is None: delim = DELIM
    code = compact_value(value, str=str)
    lines = code.splitlines()
    if compact_branches(value, delim=delim, str=str):
        return ("\n" + delim).join([""] + lines)
    else:
        return " " + "\n".join(lines)

def compact_node(node, name_func, enum_func):
    name = name_func(node)
    items = enum_func(node)
    if not items:
        return name
    elif len(items) == 1:
        return name + " " + items[0]
    else:
        lines = [name + ":"]
        for item in items:
            for line in item.splitlines():
                lines.append(DELIM + line)
        return "\n".join(lines)
