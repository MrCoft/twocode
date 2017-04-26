from twocode.context.Objects import *

def gen_node_types(context, node_types):
    def gen_embed(cls):
        def f(vars):
            return context.construct(cls, ([], {name: context.wrap_value(value) for name, value in vars.items()}))
        return f
    def gen_repr(node_type):
        def f(this):
            return repr(context.unwrap_code(this))
        return f
    scope = {}
    embed = {}
    for type_name, node_type in node_types.items():
        cls = Class()
        cls.__name__ = type_name
        scope[type_name] = cls

        for var in node_type.vars:
            cls.__fields__[var.name] = context.wrap_value(None if not var.list else []) ##

        cls.__fields__["__repr__"] = Func(native=gen_repr(node_type), args=[Arg("this", cls)])

        def init(this, **kwargs):
            for key, value in kwargs.items():
                this[key] = context.wrap_value(value)
        cls.__fields__["__init__"] = Func(native=init, args=[Arg("this", cls)]) # why inherit

        embed[type_name] = gen_embed(cls)

    def wrap_code(node):
        node_type = type(node)
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
        type_name = node.__type__.__name__
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

    return scope