from twocode.context.Operators import *
from twocode import Utils
import twocode.utils.String
import inspect

def add_types(context):
    Type, Func, Arg = [context.obj[name] for name in "Type Func Arg".split()]
    def gen_type(name):
        type = context.obj.Type()
        context.builtins[name] = type
        return type
    def attach(type, name, **kwargs):
        def wrap(func):
            type.__fields__[name] = Func(native=func, **kwargs)
        return wrap

    Null = gen_type("Null")
    Dynamic = gen_type("Dynamic")

    Bool = gen_type("Bool")
    Int = gen_type("Int")
    Float = gen_type("Float")
    String = gen_type("String")
    List = gen_type("List")
    Map = gen_type("Map")
    Set = gen_type("Set")

    Dynamic.__base__ = Map

    def pass_init(type, func):
        @attach(type, "__new__", return_type=type)
        def new():
            return context.obj.Object(type=type, this=func())
        signature = inspect.signature(func)
        @attach(type, "__init__", args=[Arg("this", type=type)] + [Arg(arg.name, type=Dynamic) for arg in signature.parameters.values()])
        def init(this, *args, **kwargs):
            this.__this__ = func(*args, **kwargs)
            # rm use of this in others
    pass_init(Null, lambda: None)
    pass_init(Dynamic, lambda val=None: {} if val is None else val)
    pass_init(Bool, lambda val=False: val)
    pass_init(Int, lambda val=0: val)
    pass_init(Float, lambda val=0.0: val)
    pass_init(String, lambda val="": val)
    pass_init(List, lambda val=None: [] if val is None else val)
    pass_init(Map, lambda val=None: {} if val is None else val)
    pass_init(Set, lambda val=None: set() if val is None else val)

    def pass_repr(type, func):
        type.__fields__["__repr__"] = Func(native=func, args=[Arg("this", type)], return_type=String)
    pass_repr(Null, lambda obj: "null")
    # dynamic repr to itself
    pass_repr(Bool, lambda obj: "true" if obj else "false")
    pass_repr(Int, lambda obj: repr(obj))
    pass_repr(Float, lambda obj: repr(obj))
    pass_repr(String, lambda obj: twocode.utils.String.escape(obj))
    pass_repr(List, lambda obj: "[{}]".format(", ".join(context.unwrap_value(context.builtins.repr.native(item)) for item in obj)))
    pass_repr(Map, lambda obj: "[{}]".format(", ".join(["{}: {}".format(context.unwrap_value(context.builtins.repr.native(key)), context.unwrap_value(context.builtins.repr.native(value))) for key, value in obj.items()])))
    pass_repr(Set, lambda obj: "@set {{}}".format(", ".join([context.unwrap_value(context.builtins.repr.native(item)) for item in obj]))) # to short func

    def pass_from(type):
        def wrap(func):
            type.__fields__["__from__"] = Func(native=func, args=[Arg("obj", Dynamic)], return_type=type)
        return wrap
    @pass_from(Dynamic)
    def dynamic_from(obj):
        return obj
    @pass_from(Bool)
    def bool_from(obj):
        if obj is not None:
            return True
        return False
    @pass_from(Float)
    def float_from(obj):
        if isinstance(obj, int):
            return obj
        raise TypeError()
    @pass_from(String)
    def string_from(obj):
        obj = context.wrap_value(obj)
        impl = context.defines(obj, "__str__")
        if impl:
            return context.call(impl, ((), {}))
        impl = context.defines(obj, "__repr__")
        if impl:
            return context.call(impl, ((), {}))
        return "<path.A object at id>"

    ops = Utils.merge_dicts(*(Utils.invert_dict(dict) for dict in [op_math, op_compare, op_unary, op_assign]))
    def pass_op(type, name, b_type=None, return_type=None):
        op = ops[name]
        func = Func(native=lambda a, b: eval("a {} b".format(op)) if b_type else lambda a: eval("{}a".format(op)))
        func.args = [Arg("a", type)]
        if b_type:
            func.args.append(Arg("b", b_type))
        func.return_type = return_type
        type.__fields__[name] = func

    for group in [
        Utils.redict(op_math, remove="/".split()),
        op_compare,
    ]:
        for symbol, name in group.items():
            pass_op(Int, name, Int, Int)
    for symbol, name in op_unary.items():
        pass_op(Int, name, return_type=Int)

    for group in [
        Utils.redict(op_math, add="+-*/"),
        op_compare,
    ]:
        for symbol, name in group.items():
            pass_op(Float, name, Float, Float)
    for symbol, name in Utils.redict(op_unary, remove="~".split()).items():
        pass_op(Float, name, return_type=Float)

    for type in String, List:
        for args in [
            ("__add__", type, type),
            ("__mul__", Int, type),
        ]:
            pass_op(type, *args)
    for type in List, Set:
        for args in [
            ("__and__", type, type),
            ("__or__", type, type),
            ("__xor__", type, type),
        ]:
            pass_op(type, *args)

    # pass_op(String, op_assign["+="], "List", "List")    += not working

    def hash(index):
        if index.__hash__ is not None:
            return index
        else:
            return id(index)
    def getitem(this, index):
        return this[hash(index)]
    def setitem(this, index, value):
        this[hash(index)] = value
    def pass_index(type, index_type, value_type):
        type.__fields__["__getitem__"] = Func(native=getitem, args=[
            Arg("this", type),
            Arg("index", index_type),
        ], return_type=value_type)
        type.__fields__["__setitem__"] = Func(native=setitem, args=[
            Arg("this", type),
            Arg("index", index_type),
            Arg("value", value_type),
        ])
    # name -> name<T>
    for type in String, List, Map:
        pass_index(type, Int, None)
    # impl
    @attach(Dynamic, "__getattribute__", args=[Arg("this", Dynamic), Arg("name", String)], return_type=Dynamic)
    def dynamic_getattribute(this, name):
        return this.__this__[name]
    @attach(Dynamic, "__getattribute__", args=[Arg("this", Dynamic), Arg("name", String), Arg("value", Dynamic)])
    def dynamic_setattribute(this, name, value):
        this.__this__[name] = value