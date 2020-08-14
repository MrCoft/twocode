from . import Transpiler
import random
import builtins
from twocode import utils
from twocode.lang.source import pack_args

LOG = set()
LOG.add("DEBUG")

class Scope:
    def __init__(self, desc=None, parent=None):
        self.vars = {}
        self.desc = desc
        self.parent = parent
        self.children = []
        if parent:
            parent.children.append(self)
        Transpiler.current.all_scopes.append(self)
    class Var:
        def __init__(self, type=None):
            self.type = type
    def __setitem__(self, name, var):
        self.vars[name] = var
    def __str__(self):
        return str({name: var.type for name, var in self.vars.items()})
    def full_desc(self):
        items = []
        scope = self
        while scope:
            if scope.desc:
                items.insert(0, scope.desc)
            scope = scope.parent
        return ".".join(items) if items else "<env>"
    def flatten(self):
        vars = {}
        scope = self
        while scope:
            for name, var in scope.vars.items():
                vars.setdefault(name, var)
            scope = scope.parent
        return vars
    def unique_name(self):
        vars = self.flatten()
        for i in range(16):
            name = "_{:x}".format(i)
            if name not in vars:
                return name
        ord = 2
        while True:
            for _ in range(4 ** ord):
                i = random.getrandbits(4 * ord)
                name = "_{{:0{}x}}".format(ord).format(i)
                if name not in vars:
                    return name
            ord += 1
    def find_name(self, name):
        scope = self
        while scope:
            if name in scope.vars:
                break
            scope = scope.parent
        return scope

def discover_classes(env=None):
    from . import import_code_env
    import_code_env()
    if env is None:
        env = c.scope.get_env()
    transp.env = env

    transp.all_scopes = []
    transp.all_classes = []
    transp.class_to_scope = {}

    builtins = call(env, "builtins").values()
    def search_module(module, scope):
        for name in sorted(module.__this__):
            obj = module.__this__[name].value
            scope[name] = Scope.Var(obj.__type__)
            if obj.__type__ is Module:
                search_module(obj, Scope(name, parent=transp.env_scope))
            if obj.__type__ is Class and obj not in builtins:
                transp.all_classes.append(obj)
                class_scope = Scope(name, parent=scope)
                transp.class_to_scope[obj] = class_scope
    transp.env_scope = Scope()
    search_module(env, transp.env_scope)

    if "DEBUG" in LOG:
        # path = qualname(obj) - tree
        print(*[op.qualname(type).split(".")[-1] for type in transp.all_classes], sep=", ")
    # prevent loops

def map_code():
    from . import import_code_env
    import_code_env()

    transp.all_nodes = []
    transp.all_codes = []
    transp.node_to_scope = {}
    transp.args_scopes = {}
    transp.scope_to_code = {} # NOTE: used by some code_edit variant

    preview_node = lambda node: "<{}>".format(utils.interface.preview(repr(node).splitlines()[0], 22, rstrip=True))
    def preview_func(f, cls, name):
        bound = c.bound(f, cls)
        args = []
        for arg in f.args if not bound else f.args[1:]:
            arg_code =\
                pack_args(arg.pack) +\
                ("macro " if arg.macro_ else "") +\
                arg.name
            args.append(arg_code)

        return "{}({})".format(
            name,
            utils.interface.preview(
                ", ".join(args),
            20, rstrip=True),
        )
    def search_nodes(node, scope):
        transp.all_nodes.append(node)
        transp.node_to_scope[node] = scope

        type_name = builtins.type(node).__name__
        code = None
        if type_name in "if_block for_loop while_loop with_block expr_block".split():
            code = node.block
        if type_name in "if_chain".split():
            code = node.else_block # wat
        if code:
            transp.all_codes.append(code)

        for child in node.children:
            if child is not code:
                search_nodes(child, scope)
            else:
                search_nodes(child, Scope(preview_node(node), parent=scope))
    for cls in transp.all_classes:
        class_scope = transp.class_to_scope[cls]
        for name, field in sorted(cls.__fields__.items()):
            if field.__type__ is Attr:
                class_scope[name] = Scope.Var(field.cls)
            if field.__type__ is Func:
                args_scope = Scope(preview_func(field, cls, name), parent=class_scope)
                for arg in field.args:
                    args_scope[arg.name] = Scope.Var(arg.cls)
                transp.args_scopes[field] = args_scope
                search_nodes(field.code, Scope(parent=args_scope))
                class_scope[name] = Scope.Var(Func)

    if "DEBUG" in LOG:
        # print(len(all_nodes), "nodes")
        print(*[repr(code) for code in transp.all_codes], sep="\n" * 2)

    with c.FrameContext([transp.env]): # why tho. and it's not correct to eval types that way
        for node in transp.all_nodes:
            type_name = builtins.type(node).__name__
            if type_name == "stmt_var":
                decl = node.declares.decl
                type = c.eval(decl.type) if decl.type else None
                # if node.assign_chain:
                #var assign = node.assign_chain[0]
                # attr.default_ = assign.tuple
                transp.node_to_scope[node][decl.id] = Scope.Var(type)
            if type_name == "func_def":
                transp.node_to_scope[node][node.id] = Scope.Var(Func)
            if type_name == "class_def":
                transp.node_to_scope[node][node.id] = Scope.Var(Class)
            if type_name == "for_loop":
                transp.node_to_scope[node.block][node.names.id] = Scope.Var()
            if type_name == "with_block": # if as, multiple
                transp.node_to_scope[node.block][node.id] = Scope.Var()

    if "DEBUG" in LOG:
        print(*transp.all_scopes, sep="\n" * 2)

        for node in transp.all_codes:
            lines = []
            scope = transp.node_to_scope[node]
            while scope:
                lines.insert(0, repr(scope.vars))
                scope = scope.parent
            print("\n".join(lines))
            print(repr(node))
            print("\n" * 2)

# default_=node.expr
# same for attr and func arg defaults. turn ALL of these to typing?
# default_ - with block, attr? no, that's the job of typing to figure that out
    # i don't think it has to link back to scopes, it's more that any time you mention a scope,
    # we should figure out what slot it belongs to
    # which CAN BE a SCOPE SLOT. ALL OF THEM. AS WELL AS NODES

# SCOPE - include __defaults__ ?
