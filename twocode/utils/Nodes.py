import twocode.Utils
import twocode.utils.Code
import copy

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
                lines.append(".\t{}".format(line))
        return "\n".join(lines)
    def __len__(self):
        total = 0
        for child in self.children:
            if isinstance(child, Node):
                total += len(child)
            else:
                total += 1
        return total

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

class Var:
    def __init__(self, name, type=None, list=False):
        self.name = name
        self.type = type
        self.list = list
def node_gen(vars, name):
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
            return compact_node(self, delim=".\t", arg_vars=[var.name for var in GenNode.vars])
    GenNode.vars = vars
    GenNode.__name__ = name
    return GenNode
def regen_types(input_types):
    node_types = {}
    for type_name, input_type in input_types.items():
        node_type = node_gen(copy.deepcopy(input_type.vars), type_name)
        node_types[type_name] = node_type

    def gen_retype(node_type):
        def f(node):
            return node_type(**node.__dict__)
        return f
    type_map = {}
    for type_name, node_type in node_types.items():
        type_map[type_name] = gen_retype(node_type)
    return node_types, type_map

def compact_value(value):
    if type(value) is str:
        return repr(value)
    if type(value) is list:
        return "\n".join(str(item) for item in value)
    else:
        return str(value)
def compact_branches(value, delim=".\t"):
    if type(value) is str:
        return False
    if type(value) is list:
        return True
    lines = str(value).splitlines()
    return len([line for line in lines if not line.startswith(delim)]) > 1
def compact_block(value, branches=None, delim=".\t"):
    code = compact_value(value)
    if branches is None:
        branches = compact_branches(value, delim)
    lines = code.splitlines()
    if branches:
        return ("\n" + delim).join([""] + lines)
    else:
        return "\n".join(lines)
def compact_node(node, delim=".\t", arg_vars=None):
    format_value = lambda value: compact_block(value, delim=delim)
    name = type(node).__name__
    if len(node.__dict__) == 1:
        node = next(iter(node.__dict__.values()))
        if isinstance(node, Node):
            return name + " " + str(node)
        else:
            # REASON: to have ":" before repr(value), and to do lists of all sizes the same way
            return name + ": " + compact_block(node, delim=delim)
    lines = [
        "{}: {}".format(key, format_value(value)) for key, value in sorted(twocode.Utils.redict(node.__dict__, arg_vars).items())
    ] + [
        "{}: {}".format(key, format_value(node.__dict__[key])) for key in arg_vars
    ]
    return name + ":" + compact_block(lines, True, delim)
