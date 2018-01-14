import builtins
from twocode import Utils
from twocode.utils.Nodes import compact_node

def add_node_types(context):
    Class, Func, Arg = [context.obj[name] for name in "Class, Func, Arg".split(", ")]
    String, List = [context.basic_types[name] for name in "String, List".split(", ")]
    wraps = context.native_wraps

    node_types = context.parser.node_types
    context.node_types = Utils.Object()

    def node_init(this, **kwargs):
        for key, value in kwargs.items():
            this[key] = context.wrap(value)
        # TODO: proper positional arguments
    @wraps(wrap_return=True)
    def node_to_string(this):
        return repr(context.unwrap_code(this))
    @wraps(wrap_return=True)
    def node_repr(this):
        return "macro " + context.unwrap(this.__type__.__fields__["to_string"].native(this))
    @wraps(wrap_return=True)
    def node_tree(this):
        return tree_str(context.unwrap_code(this))
    def tree_str(node):
        node_type = builtins.type(node)
        type_name = node_type.__name__
        if type_name not in node_types:
            return str(node)
        return compact_node(node, delim=".\t".replace("\t", " " * (4 - 1)), arg_vars=[var.name for var in builtins.type(node).vars], str=tree_str)
    @wraps(wrap_return=True)
    def node_get_children(this):
        return this.children

    embed = {}
    type_to_name = {}
    def gen_embed(type):
        def f(vars):
            return context.construct(type, ([], {name: context.wrap(value) for name, value in vars.items()}))
            # doesn't this require a deep list?
        return f

    for type_name, node_type in node_types.items():
        type = Class()
        context.node_types[type_name] = type
        for var in node_type.vars:
            type.__fields__[var.name] = context.obj.Var() # wrap(None if not var.list else [])
        type.__fields__["__init__"] = Func(native=node_init, args=[Arg("this", type), Arg("kwargs", pack="kwargs")])
        type.__fields__["to_string"] = Func(native=node_to_string, args=[Arg("this", type)], return_type=String)
        type.__fields__["repr"] = Func(native=node_repr, args=[Arg("this", type)], return_type=String)
        type.__fields__["tree"] = Func(native=node_tree, args=[Arg("this", type)], return_type=String)
        type.__fields__["get_children"] = Func(native=node_get_children, args=[Arg("this", type)], return_type=List)
        # NOTE:
        # chooses to require String
        # better than including node types in temp scope, they aren't used anywhere else

        # a func that sets their initial vars?
        # bring pack proper types -

        embed[type_name] = gen_embed(type)
        type_to_name[type] = type_name

    def wrap_code(node):
        node_type = builtins.type(node)
        type_name = node_type.__name__
        if type_name not in node_types:
            return context.wrap(node)

        vars = {}
        for var in node_type.vars:
            if not var.list:
                vars[var.name] = context.wrap_code(node.__dict__[var.name])
            else:
                vars[var.name] = context.wrap([context.wrap_code(sub_child) for sub_child in node.__dict__[var.name]])

        return embed[type_name](vars)
    context.wrap_code = wrap_code

    def unwrap_code(node):
        type_name = type_to_name.get(getattr(node, "__type__", None))
        if type_name not in node_types:
            return context.unwrap(node)
        node_type = node_types[type_name]

        vars = {}
        for var in node_type.vars:
            if not var.list:
                vars[var.name] = context.unwrap_code(node.__dict__[var.name])
            else:
                vars[var.name] = [context.unwrap_code(sub_child) for sub_child in node.__dict__[var.name].__this__]

        return node_type(**vars)
    context.unwrap_code = unwrap_code