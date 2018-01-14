from twocode import Utils
import builtins

op_math = {
    "+": "add",
    "-": "sub",
    "*": "mul",
    "/": "div",
    "%": "mod",
    "&": "and",
    "|": "or",
    "^": "xor",
    "<<": "lshift",
    ">>": "rshift",
    "**": "pow",
    "//": "floordiv",
}
op_compare = {
    "==": "eq",
    "!=": "ne",
    "<": "lt",
    ">": "gt",
    "<=": "le",
    ">=": "ge",
}
op_unary = {
    "+": "pos",
    "-": "neg",
    "~": "invert",
}
op_assign = {
    "=": "mov",
    "+=": "iadd",
    "-=": "isub",
    "*=": "imul",
    "/=": "idiv",
    "%=": "imod",
    "&=": "iand",
    "|=": "ior",
    "^=": "ixor",
    "<<=": "ilshift",
    ">>=": "irshift",
    "**=": "ipow",
    "//=": "ifloordiv",
}
def increment(obj):
    obj.__this__ += 1
def decrement(obj):
    obj.__this__ -= 1

def add_operators(context):
    wraps = context.native_wraps

    context.operators = Utils.Object()
    def create(signature):
        def wrap(func):
            f = context.obj.Func(native=func, sign=signature)
            context.operators[func.__name__] = f
        return wrap

    @create("(obj:Dynamic)->String")
    def repr(obj):
        """
            CODE REPR PROBLEM:
            Func, Class now have a more simple repr
            full repr moved to Type.source

            i absolutely want source code to be accessible easily
            but repr is meant to be reasonable
            any large class would print a thousand lines in the console
            when you only wanted to know its path

            OBJECT REPR PROBLEM:
            deref(ptr, type) now <type object>

            it's dangerous
            an address in object_repr would tell you whether objects are unique
            but it's ugly, it makes containers long
            it's not what you want to see while debugging
        """
        repr = context.impl(obj.__type__, "repr")
        if repr:
            return context.call(repr, ([obj], {}))
        return context.wrap(context.object_repr(obj))
        # no more iter error at iter
    def object_repr(obj):
        qualname = context.unwrap(context.operators.qualname.native(obj.__type__))
        return "<{} object>".format(qualname) if qualname else "<unknown object>"
    context.object_repr = object_repr
    def shell_repr(obj):
        if obj is None or obj.__type__ is context.basic_types.Null:
            # REASON:
            # don't print null
            # "__this__" check detects basics but doesn't work for null
            obj = None
        else:
            obj = context.unwrap(context.operators.repr.native(obj))
        return obj
    context.shell_repr = shell_repr
    @create("(obj:Dynamic)->String")
    @wraps(wrap_return=True)
    def qualname(obj):
        qualnames = context.scope.get_env().__qualnames__
        try:
            return context.call(context.impl(qualnames.__type__, "__getitem__"), ([qualnames, obj], {}))
        except KeyError:
            return None
        # from current scope?
    def hash(key):
        impl = context.impl(key.__type__, "hash")
        if impl:
            return context.unwrap(context.call(impl, ([key], {})))
        else:
            return id(key)
    context.hash = hash
    # to func? like all others?

    def gen_binop(op, rename=None):
        if rename is None: rename = op
        name = "__{}__".format(op)
        def func(a, b):
            impl = context.impl(a.__type__, name)
            if not impl:
                raise TypeError("cannot {} {} and {}".format(
                    op,
                    context.unwrap(context.operators.qualname.native(a.__type__)),
                    context.unwrap(context.operators.qualname.native(b.__type__)),
                ))
            return context.call(impl, ([a, b], {}))
        f = context.obj.Func(native=func, sign="(a:Dynamic, b:Dynamic)->Dynamic")
        context.operators[rename] = f
    for op in "add sub mul div mod".split():
        gen_binop(op)
    gen_binop("and", rename="and_")
    gen_binop("or", rename="or_")
    gen_binop("xor", rename="xor")
    # NOTE: boolean operators aren't customizable, they simply convert to Bool
    for op in "lshift rshift pow floordiv".split():
        gen_binop(op)

    def binop(func):
        f = context.obj.Func(native=func, sign="(a:Dynamic, b:Dynamic)->Dynamic")
        context.operators[func.__name__] = f
    @binop
    def eq(a, b):
        impl = context.impl(a.__type__, "__eq__")
        if impl:
            return context.call(impl, ([a, b], {}))
        return context.wrap(a is b)
    @binop
    def ne(a, b):
        impl = context.impl(a.__type__, "__ne__")
        if impl:
            return context.call(impl, ([a, b], {}))
        return context.wrap(not context.unwrap(context.operators.eq.native(a, b)))
    for op in "lt gt le ge".split():
        gen_binop(op)

    def gen_unnop(op):
        name = "__{}__".format(op)
        def func(obj):
            impl = context.impl(obj.__type__, name)
            if not impl:
                raise TypeError("cannot {} {}".format(
                    op,
                    context.unwrap(context.operators.qualname.native(obj.__type__)),
                ))
            return context.call(impl, ([obj], {}))
        f = context.obj.Func(native=func, sign="(obj:Dynamic)->Dynamic")
        context.operators[op] = f
    for op in "pos neg invert".split():
        gen_unnop(op)

    @create("(obj:Dynamic)->Bool")
    def bool(obj):
        if obj.__type__ is context.basic_types.Bool:
            return obj
        try:
            pass # return context.convert(obj, context.basic_types.Bool)
        except context.exc.ConversionError:
            pass
        return context.wrap(obj.__type__ is not context.basic_types.Null)
    @create("(obj:Dynamic)->String")
    def string(obj):
        # weird. cyclic.
        if obj.__type__ is context.basic_types.String:
            return obj
        impl = context.impl(obj.__type__, "to_string")
        if impl:
            return context.call(impl, ([obj], {}))
        return context.operators.repr.native(obj)
    # conversion will be done using something like cast

    @create("(obj:Dynamic)")
    def iter(obj):
        while True:
            has_next = context.impl(iter.__type__, "has_next")
            next = context.impl(iter.__type__, "next")
            if has_next and next:
                return obj
            while True:
                impl = context.impl(iter.__type__, "iter")
                if impl:
                    iter = context.call(impl, ([iter], {}))
                    break
                impl = context.impl(iter.__type__, "__getitem__")
                if impl and context.hasattr(iter, "length"):
                    iter = iter # iter over
                    break
                raise TypeError("{} object is not iterable".format(builtins.repr(context.unwrap(context.operators.qualname.native(iter.__type__))))) #
            has_next = context.impl(iter.__type__, "has_next")
            next = context.impl(iter.__type__, "next")

        has_next = context.obj.BoundMethod(iter, has_next)
        next = context.obj.BoundMethod(iter, next)

    @create("(obj:Dynamic, name:String)->Bool")
    @wraps("name", wrap_return=True)
    def hasattr(obj, name):
        return context.hasattr(obj, name)
    @create("(obj:Dynamic, name:String)->Dynamic")
    @wraps("name")
    def getattr(obj, name):
        return context.getattr(obj, name)
    @create("(obj:Dynamic, name:String, value:Dynamic)")
    @wraps("name")
    def setattr(obj, name, value):
        return context.setattr(obj, name, value)

    @create("(obj:Dynamic, key:Dynamic)->Dynamic")
    def getitem(obj, key):
        impl = context.impl(obj.__type__, "__getitem__")
        if not impl:
            raise TypeError("{} object is not a container".format(builtins.repr(context.unwrap(context.operators.qualname.native(obj.__type__)))))
        return context.call(impl, ([obj, key], {})) #
    @create("(obj:Dynamic, key:Dynamic, value:Dynamic)")
    def setitem(obj, key, value):
        impl = context.impl(obj.__type__, "__setitem__")
        if not impl:
            raise TypeError("{} object is not a container".format(builtins.repr(context.unwrap(context.operators.qualname.native(obj.__type__)))))
        return context.call(impl, ([obj, key, value], {}))
    @create("(obj:Dynamic, key:Dynamic)")
    def delitem(obj, key):
        pass

    @create("(obj:Dynamic, item:Dynamic)->Bool")
    def contains(obj, item):
        impl = context.impl(obj.__type__, "contains")
        # bool impl
        if not impl:
            # or smth
            raise TypeError("{} object is not a container".format(builtins.repr(context.unwrap(context.operators.qualname.native(obj.__type__)))))
        result = context.call(impl, ([obj, item], {})) # all instances of call,... getattr... how do i store the keys? !!!
        # method
        result = context.operators.bool.native(result)
        return result