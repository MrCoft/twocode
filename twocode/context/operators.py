from twocode import utils
import builtins
from twocode.utils.string import escape

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
keyword_ops = {
    "add": "add_",
    "or": "or_",
}
def increment(obj):
    obj.__this__ += 1
def decrement(obj):
    obj.__this__ -= 1

def add_operators(context):
    Object, Func = [context.obj[name] for name in "Object, Func".split(", ")]
    Null, Bool, String = [context.basic_types[name] for name in "Null, Bool, String".split(", ")]
    w, uw, r, dr, ops = [context.type_magic[name] for name in "w, uw, r, dr, op".split(", ")]
    wraps = context.native_wraps

    context.operators = utils.Object()
    def create(signature):
        def wrap(func):
            context.operators[func.__name__] = Func(native=func, sign=signature)
        return wrap

    @create("(obj:Object)->String")
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
        repr = context.impl(obj.__type__, "__repr__")
        if repr:
            return context.call(repr, ([obj], {}))
        return w@ context.default_repr(obj)
        # no more iter error at iter
    def default_repr(obj):
        qualname = ops.qualname(r(context.objects.Class)@ obj.__type__)
        return "<{} object>".format(qualname) if qualname else "<unknown object>"
    context.default_repr = default_repr
    def safe_repr(obj):
        if isinstance(obj, context.obj.Ref.Object):
            obj = r@ obj
        if not isinstance(obj, context.obj.Ref):
            return builtins.repr(obj)
        try:
            return ops.repr(obj)
        except: pass
        if builtins.hasattr(context, "basic_types"):
            for qualname, type in context.basic_types.items():
                if obj.__type__ is type:
                    return builtins.repr(obj.__this__)
        if builtins.hasattr(context, "get_builtins"):
            for qualname, type in context.get_builtins().items():
                if obj.__type__ is type:
                    return "<{} object>".format(qualname)
        return "<unknown object>"
    context.safe_repr = safe_repr
    def shell_repr(obj):
        if obj is None or obj.__type__ is Null:
            # REASON:
            # don't print null
            # "__this__" check detects basics but doesn't work for null
            obj = None
        else:
            obj = ops.repr(obj)
        return obj
    context.shell_repr = shell_repr
    @create("(obj:Object)->String")
    @wraps(result=True)
    def qualname(obj):
        qualnames = context.AttrRefs(r(context.scope_types.Env)@ context.scope.get_env()).__qualnames__
        try:
            return ops.getitem(qualnames, obj)
        except KeyError:
            return None
        # from current scope?
    @create("(obj:Object)->Int")
    @wraps(result=True)
    def hash(key):
        impl = context.impl(key.__type__, "__hash__")
        if impl:
            return uw@ context.call(impl, ([key], {}))
        else:
            return id(key.__refobj__)

    def gen_binop(op):
        name = "__{}__".format(op)
        def func(a, b):
            impl = context.impl(a.__type__, name)
            if not impl:
                raise TypeError("cannot {} {} and {}".format(op, ops.qualname(a.__type__), ops.qualname(b.__type__)))
            return context.call(impl, ([a, b], {}))
        context.operators[keyword_ops.get(op, op)] = Func(native=func, sign="(a:Object, b:Object)->Object")
    for op in "add sub mul div mod".split():
        gen_binop(op)
    gen_binop("and")
    gen_binop("or")
    gen_binop("xor")
    # NOTE: boolean operators aren't customizable, they simply convert to Bool
    for op in "lshift rshift pow floordiv".split():
        gen_binop(op)

    def binop(func):
        context.operators[func.__name__] = Func(native=func, sign="(a:Object, b:Object)->Object")
    @binop
    def eq(a, b):
        impl = context.impl(a.__type__, "__eq__")
        if impl:
            return context.call(impl, ([a, b], {}))
        return w@ (a is b)
    @binop
    def ne(a, b):
        impl = context.impl(a.__type__, "__ne__")
        if impl:
            return context.call(impl, ([a, b], {}))
        return w@ (not ops.eq(a, b))
    for op in "lt gt le ge".split():
        gen_binop(op)

    def gen_unop(op):
        name = "__{}__".format(op)
        def func(obj):
            impl = context.impl(obj.__type__, name)
            if not impl:
                raise TypeError("cannot {} {}".format(op, ops.qualname(obj.__type__)))
            return context.call(impl, ([obj], {}))
        context.operators[op] = Func(native=func, sign="(obj:Object)->Object")
    for op in "pos neg invert".split():
        gen_unop(op)

    @create("(obj:Object)->Bool")
    def bool(obj):
        if obj.__type__ is Bool:
            return obj
        try:
            convert = context.impl(obj.__type__, "__to__")
            if convert:
                return context.call(convert, ([obj, Bool], {}))
        except context.exc.ConversionError:
            pass
        return w@ (obj.__type__ is not Null)
    @create("(obj:Object)->String")
    def string(obj):
        if obj.__type__ is String:
            return obj
        # __to__?
        impl = context.impl(obj.__type__, "__str__")
        if impl:
            return context.call(impl, ([obj], {}))
        return context.operators.repr.native(obj)
    # conversion will be done using something like cast

    @create("(obj:Object)")
    def iter(obj):
        has_next = context.impl(obj.__type__, "has_next")
        next = context.impl(obj.__type__, "next")
        if has_next and next:
            return obj
        impl = context.impl(obj.__type__, "__iter__")
        if impl:
            obj = context.call(impl, ([obj], {}))
            return obj
        impl = context.impl(obj.__type__, "__getitem__")
        if impl and context.hasattr(obj, "length"): # in fields?
            obj = obj # iter over
            return obj
        raise TypeError("{} object is not iterable".format(escape(ops.qualname(obj.__type__)))) #
    @create("(obj:Object)->Int")
    def len(obj):
        if context.hasattr(obj, "length"):
            # in fields?
            impl = context.impl(obj.__type__, "length")
            return context.call(impl, ([obj], {}))
        raise TypeError("{} object has no length".format(escape(ops.qualname(obj.__type__))))

    @create("(obj:Object, name:String)->Bool")
    @wraps("name", result=True)
    def hasattr(obj, name):
        return context.hasattr(obj, name)
    @create("(obj:Object, name:String)->Object")
    @wraps("name")
    def getattr(obj, name):
        return context.getattr(obj, name)
    @create("(obj:Object, name:String, value:Object)")
    @wraps("name")
    def setattr(obj, name, value):
        return context.setattr(obj, name, value)

    @create("(obj:Object, key:Object)->Object")
    def getitem(obj, key):
        impl = context.impl(obj.__type__, "__getitem__")
        if not impl:
            raise TypeError("{} object is not a container".format(escape(ops.qualname(obj.__type__))))
        return context.call(impl, ([obj, key], {})) #
    @create("(obj:Object, key:Object, value:Object)")
    def setitem(obj, key, value):
        impl = context.impl(obj.__type__, "__setitem__")
        if not impl:
            raise TypeError("{} object is not a container".format(escape(ops.qualname(obj.__type__))))
        return context.call(impl, ([obj, key, value], {}))
    @create("(obj:Object, key:Object)")
    def delitem(obj, key):
        pass

    @create("(obj:Object, item:Object)->Bool")
    def contains(obj, item):
        impl = context.impl(obj.__type__, "__contains__")
        # bool impl
        if not impl:
            # or smth
            raise TypeError("{} object is not a container".format(escape(ops.qualname(obj.__type__))))
        result = context.call(impl, ([obj, item], {})) # all instances of call,... getattr... how do i store the keys? !!!
        # method
        result = context.operators.bool.native(result)
        return result

    @create("(code:String, scope:Object=null, ?file:String)->Object")
    @wraps("code", "file")
    def eval(code=None, scope=None, file=None):
        if file:
            code = builtins.open(file, encoding="utf-8").read()
            # context.declare("__file__", context.wrap(file), String)
            # in the scope?!?? not here, not in the module
        if isinstance(code, str):
            code = context.parse(code)
        else:
            code = context.unwrap_code(code)
        if scope.__type__ is not Null:
            impl = context.impl(scope.__type__, "__code__")
            # what if wrong args? error?
            if impl and impl.args and impl.args[1].macro_:
                return context.call(impl, ([scope, context.wrap_code(code)], {}))
            if scope.__type__ is context.basic_types.List:
                frame = uw@ scope
                if not frame or not context.extends(frame[0].__type__, context.scope_types.Env):
                    frame.insert(0, context.scope.get_env())
            elif context.extends(scope.__type__, context.scope_types.Env):
                frame = [scope]
            else:
                try:
                    scope = context.convert(scope, context.scope_types.Scope)
                except context.exc.ConversionError:
                    scope = Object(context.scope_types.ObjectScope, object=scope)
                frame = context.frame.copy()
                frame.append(scope.__refobj__)
                if scope.__type__ is context.scope_types.ObjectScope:
                    frame.append(context.obj.Ref.Object(context.scope_types.Scope, __this__={}))

            with context.FrameContext(frame):
                return context.eval(code, type="pass")
        else:
            return context.eval(code, type="pass")

    @create("(obj:Object)->Object")
    def term(obj):
        impl = context.impl(obj.__type__, "__term__")
        if impl:
            obj = context.call(impl, ([obj], {}))
        return obj
    @create("(obj:Object)->Object")
    def expr(obj):
        impl = context.impl(obj.__type__, "__expr__")
        if impl:
            obj = context.call(impl, ([obj], {}))
        return obj
    @create("(obj:Object)->Object")
    def stmt(obj):
        impl = context.impl(obj.__type__, "__stmt__")
        if impl:
            obj = context.call(impl, ([obj], {}))
        return obj
