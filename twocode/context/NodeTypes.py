import builtins

def add_node_types(context):
    node_types = context.node_types
    Type, Func = [context.obj[name] for name in "Type Func".split()]
    def gen_embed(type):
        def f(vars):
            return context.construct(type, ((), {name: context.wrap_value(value) for name, value in vars.items()}))
        return f
    context.builtins.NodeTypes = {}
    embed = {}
    type_to_name = {}
    for type_name, node_type in node_types.items():
        type = Type()
        context.builtins.NodeTypes[type_name] = type
        type_to_name[type] = type_name

        for var in node_type.vars:
            type.__fields__[var.name] = context.obj.Var()
            # type.__fields__[var.name] = context.wrap_value(None if not var.list else []) ##

        type.__fields__["__str__"] = Func(native=lambda this: repr(context.unwrap_code(this)), sign="(this:{})->String".format(type_name))
        type.__fields__["__repr__"] = Func(native=lambda this: "macro " + context.unwrap_value(this.__type__.__fields__["__str__"].native(this)), sign="(this:{})->String".format(type_name))

        def init(this, **kwargs): # out
            for key, value in kwargs.items():
                this[key] = context.wrap_value(value)
        type.__fields__["__init__"] = Func(native=init, sign="(this:{}, **kwargs)->Null".format(type_name))

        embed[type_name] = gen_embed(type)

    def wrap_code(node):
        node_type = builtins.type(node)
        type_name = node_type.__name__
        if type_name not in node_types:
            return context.wrap_value(node)

        vars = {}
        for var in node_type.vars:
            if not var.list:
                vars[var.name] = context.wrap_code(node.__dict__[var.name])
            else:
                vars[var.name] = context.wrap_value([context.wrap_code(sub_child) for sub_child in node.__dict__[var.name]])

        return embed[type_name](vars)
    context.wrap_code = wrap_code

    def unwrap_code(node):
        type_name = type_to_name.get(getattr(node, "__type__", None))
        if type_name not in node_types:
            return context.unwrap_value(node)
        node_type = node_types[type_name]

        vars = {}
        for var in node_type.vars:
            if not var.list:
                vars[var.name] = context.unwrap_code(node.__dict__[var.name])
            else:
                vars[var.name] = [context.unwrap_code(sub_child) for sub_child in node.__dict__[var.name].__this__]

        return node_type(**vars)
    context.unwrap_code = unwrap_code