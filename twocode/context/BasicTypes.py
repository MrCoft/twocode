from twocode.context.Operators import *
from twocode.context.Objects import *
from twocode import Utils
import twocode.utils.String

def gen_types(context):
    ops = Utils.merge_dicts(*(Utils.invert_dict(dict) for dict in [op_math, op_compare, op_unary, op_assign]))
    def gen_binop(op):
        def f(a, b):
            return eval("a {} b".format(op))
        return f
    def gen_unop(op):
        def f(a):
            return eval("{}a".format(op))
        return f
    def pass_op(type, func_name, b_type=None, return_type=None):
        func = Func(native=
            (gen_binop if b_type else gen_unop)(ops[func_name])
        )
        func.args = [Arg("a", type)]
        if b_type:
            func.args.append(Arg("b", context.eval(b_type)))
        func.return_type = context.eval(return_type)
        type.__fields__[func_name] = func
    def pass_repr(type, func):
        def f(this):
            return func(this)
        type.__fields__["__repr__"] = Func(native=f, args=[Arg("this", type)], return_type=context.builtins.String)
    def getitem(this, index):
        return this[index]
    def setitem(this, index, value):
        this[index] = value
        return value # a
    def pass_index(type, index_type):
        type.__fields__["__getitem__"] = Func(native=getitem, args=[
            Arg("this", type),
            Arg("index", context.eval(index_type)),
        ])
        type.__fields__["__setitem__"] = Func(native=setitem, args=[
            Arg("this", type),
            Arg("index", context.eval(index_type)),
            Arg("value", context.eval(index_type)),
        ])
    def gen_method(name):
        def f(*args, **kwargs):
            obj = context.scope['__this__'] # unwrap?
            return eval("obj.{}".format(name))(*args, **kwargs)
        return f
    def pass_method(type, name, signature, rename=None):
        if rename is None: rename = name
        method = Func(native=gen_method(name))
        method.args = [Arg("this"), type] #
        type.__fields__[rename] = method
    def pass_conv(type, retype):
        def f(): # so self should shouldnt be there? right now not as it is an invisible layer below
            this = context.scope['__this__']
            return retype(this)
        type.__fields__["__conv__"] = Func(native=f)
        pass
        # int to float

    def gen_type(name):
        type = Class()
        type.__name__ = name
        context.builtins[name] = type
        return type

    Null = gen_type("Null")
    Bool = gen_type("Bool")
    Int = gen_type("Int")
    Float = gen_type("Float")
    String = gen_type("String")
    List = gen_type("List")
    Map = gen_type("Map")
    Set = gen_type("Set")

    pass_repr(Null, lambda obj: "null")
    pass_repr(Bool, lambda obj: "true" if obj else "false")
    pass_repr(Int, lambda obj: repr(obj))
    pass_repr(Float, lambda obj: repr(obj))
    def r(obj):
        code = twocode.utils.String.escape(obj)
        return code
    pass_repr(String, r)
    def r(obj):
        items = [context.call(context.builtins.repr, ([item], {})) for item in obj]
        items = [context.unwrap_value(item) for item in items]
        return "[{}]".format(", ".join(items))
    pass_repr(List, r)
    pass_repr(Map, lambda obj: "[{}]".format(", ".join(["{}: {}".format(context.unwrap_value(context.builtins.repr.native(key)), context.unwrap_value(context.builtins.repr.native(value))) for key, value in obj.items()])))
    pass_repr(Set, lambda obj: "{{}}".format(", ".join([context.unwrap_value(context.builtins.repr.native(item)) for item in obj]))) # to short func

    def f(obj):
        if obj is not None:
            return True
        return False
    Bool.__fields__["__from__"] = Func(native=f)
    def f(obj):
        obj = context.wrap_value(obj)
        type = obj.__type__
        if "__str__" in obj.__bound__:
            return context.call(obj.__bound__["__str__"], ([], {}))
        if "__repr__" in obj.__bound__:
            return context.call(obj.__bound__["__repr__"], ([], {}))
        return "<path.A object at ID>"
    String.__fields__["__from__"] = Func(native=f)

    for dict in [
        Utils.redict(op_math, remove="/".split()),
        op_compare,
    ]:
        for symbol, func_name in dict.items():
            pass_op(Int, func_name, "Int", "Int")
    for symbol, func_name in op_unary.items():
        pass_op(Int, func_name, return_type="Int")

    for dict in [
        Utils.redict(op_math, add="+-*/"),
        op_compare,
    ]:
        for symbol, func_name in dict.items():
            pass_op(Float, func_name, "Float", "Float")
    for symbol, func_name in Utils.redict(op_unary, remove="~".split()).items():
        pass_op(Float, func_name, return_type="Float")

    # pass_op(String, op_assign["+="], "List", "List")    += not working

    # value/ref
    # @struct

    # name -> name<T>
    for type in String, List:
        pass_index(type, "Int")
    for type in String, List:
        for args in '''
            __add__ {type_name} {type_name}
            __mul__ Int {type_name}
        '''.format(type_name=type.__name__).strip().splitlines():
            pass_op(type, *args.split())
    for type in List, Set:
        for args in '''
            __and__ {type_name} {type_name}
            __or__ {type_name} {type_name}
            __xor__ {type_name} {type_name}
        '''.format(type_name=type.__name__).strip().splitlines():
            pass_op(type, *args.split())

    for args in '''
        format *Iter<String>->String
        split ->List<String>
        join Iter<String>->String
    '''.strip().splitlines():
        pass_method(String, *args.split())

    for args in '''
        append T->T push
    '''.strip().splitlines():
        pass_method(List, *args.split())