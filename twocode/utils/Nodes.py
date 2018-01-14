import twocode.Utils
import twocode.utils.Code
import functools
import builtins
import twocode.utils.String

delim = ".\t".replace("\t", " " * (4 - 1))

class Node:
    def __init__(self, **kwargs):
        self.children = []
        self.parents = []
        self.__dict__.update(kwargs)
    def __repr__(self):
        lines = [
            "{}: {}".format(key, value) for key, value in sorted(twocode.Utils.redict(self.__dict__, ["children", "parents"]).items())
        ]
        for child in self.children:
            for line in str(child).splitlines():
                lines.append(delim + line)
        return "\n".join(lines)

def free_batch(group, cond):
    fail_check = twocode.utils.Code.fail_check(lambda: len(group))
    while group and fail_check:
        batch = []
        for item in group:
            if all(not cond(item, item2) for item2 in group if item != item2):
                batch.append(item)
        for item in batch:
            group.remove(item)
        yield batch
def depend(group, cond):
    for group in free_batch(group, cond):
        for item in group:
            yield item
def inherit(node1, node2):
    return node2 in node1.parents
def substr(a, b):
    return b.find(a) >= 0

def map(enter=None, leave=None):
    def filter(tree):
        if enter:
            tree = enter(tree)
        tree.children = [filter(child) for child in tree.children]
        if leave:
            tree = leave(tree)
        return tree
    return filter

def all_common(groups):
    all = set()
    common = set()
    for group in groups:
        for item in group:
            if item in all:
                common.add(item)
            else:
                all.add(item)
    return all, common

def switch(map, key):
    def filter(tree):
        val = key(tree)
        if val in map:
            tree = map[val](tree)
        return tree
    return filter

def range_call(f):
    def filter(node, pos=0):
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
    def wrapped(tree, *args, **kwargs):
        result = f(tree, *args, **kwargs)
        return result if result else tree
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
            return compact_node(self, delim=delim, arg_vars=[var.name for var in GenNode.vars])
    GenNode.vars = vars
    GenNode.__name__ = name
    return GenNode

def compact_value(value, str=builtins.str):
    if type(value) is builtins.str:
        return twocode.utils.String.escape(value)
    elif type(value) is list:
        return "\n".join(str(item) for item in value)
    else:
        return str(value)
def compact_branches(value, delim=delim, str=builtins.str):
    if type(value) is builtins.str:
        return False
    if type(value) is list:
        return True
    lines = str(value).splitlines()
    return len([line for line in lines if not line.startswith(delim)]) > 1
def compact_block(value, branches=None, delim=delim, str=builtins.str):
    code = compact_value(value, str)
    if branches is None:
        branches = compact_branches(value, delim, str)
    lines = code.splitlines()
    if branches:
        return ("\n" + delim).join([""] + lines)
    else:
        return " " + "\n".join(lines)
def compact_node(node, delim=delim, arg_vars=None, str=builtins.str):
    format_value = lambda value: compact_block(value, delim=delim, str=str)
    name = type(node).__name__
    if len(node.__dict__) == 1:
        node = next(iter(node.__dict__.values()))
        if isinstance(node, Node):
            return name + " " + str(node)
        else:
            # REASON: to have ":" before repr(value), and to do lists of all sizes the same way
            return name + ":" + compact_block(node, delim=delim, str=str)
    lines = [
        "{}:{}".format(key, format_value(value)) for key, value in sorted(twocode.Utils.redict(node.__dict__, arg_vars).items())
    ] + [
        "{}:{}".format(key, format_value(node.__dict__[key])) for key in arg_vars
    ]
    return name + ":" + compact_block(lines, True, delim, str)
