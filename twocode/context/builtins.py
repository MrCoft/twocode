from twocode import utils
import builtins
import textwrap
import ctypes

def add_builtins(context):
    w, uw, r, dr, op = [context.type_magic[name] for name in "w, uw, r, dr, op".split(", ")]
    wraps = context.native_wraps

    context.builtins = utils.Object()
    def create(signature):
        def wrap(func):
            context.builtins[func.__name__] = context.obj.Func(native=func, sign=signature)
        return wrap

    @create("(code:String)->Object")
    @wraps("code")
    def native(code):
        code = textwrap.dedent(code).strip()
        builtins.exec(code, context.native_env.copy())
    native_env = utils.Object()
    context.native_env = native_env
    native_env.c = context
    native_env.w, native_env.uw = context.type_magic.w, context.type_magic.uw
    class WrappedScope:
        def __getattr__(self, name):
            return uw@ context.scope[name]
        def __setattr__(self, name, value):
            context.scope[name] = w@ value
    native_env.s = WrappedScope()
    def ret(obj):
        raise context.exc.Return(w@ obj)
    native_env.ret = ret
    def call(obj, method=None, *args, **kwargs):
        args = list(args)
        if method is None:
            value = context.call(obj, (args, kwargs))
        else:
            value = context.call(context.impl(obj.__type__, method), ([obj, *args], kwargs))
        value = uw@ value
        return value
    native_env.call = call
    class WrappedObject:
        def __init__(self, obj):
            self.__dict__["this"] = obj
        def __getattr__(self, name):
            obj = uw@ context.getattr(self.this, name)
            if isinstance(obj, context.obj.Ref):
                return WrappedObject(obj)
            return obj
        def __setattr__(self, name, value):
            if isinstance(value, WrappedObject):
                value = value.this
            context.setattr(self.this, name, w@ value)
        def __call__(self, *args, **kwargs):
            args = [arg if not isinstance(arg, WrappedObject) else arg.this for arg in args]
            kwargs = {name: arg if not isinstance(arg, WrappedObject) else arg.this for name, arg in kwargs.items()}
            return context.call(self.this, (args, kwargs))
        # str, repr, math operators, iter
    native_env.wo = WrappedObject
    native_env.no = lambda obj: context.obj.Object(context.std_lib.NativeObject, __this__=obj)

    @create('(*objects:Object, sep=" ", end="\\n", flush=true)')
    @wraps("sep", "end", "flush")
    def print(*objects, sep=" ", end="\n", flush=True):
        objects = [op.string(r@ obj) for obj in objects]
        builtins.print(*objects, sep=sep, end=end, flush=flush)

    # order from here

    @create("(module:Module)") # module path
    def reload(module):
        qualname = op.qualname(module)
        #if not qualname:
        #    return # exc
        env = r(context.scope_types.Env)@ context.scope.get_env()
        qualnames = context.AttrWrapper(env).__qualnames__
        qualnames.pop(id(module), None)
        builtins.print("qn", qualname)
        context.imp(qualname)
        # reuse the module object

        # not working since it's a copy

    # open -> FileStream
    @create('(file:String, mode="r", encoding="utf-8")->Object')
    @wraps("file", "mode", "encoding")
    def open(file, mode="r", encoding="utf-8"):
        return builtins.open(file, mode=mode, encoding=encoding)
    @create("(code:String, ?file:String)->Code")
    @wraps("code", "file")
    def parse(code=None, file=None):
        if file:
            code = builtins.open(file, encoding="utf-8").read()
        return context.wrap_code(context.parse(code))

    @create("(obj:Object)->Int")
    @wraps(result=True)
    def addressof(obj):
        return ctypes.addressof(obj)
    @create("(ptr:Int, type:Class)->Object")
    @wraps("ptr")
    def deref(ptr, type):
        return ctypes.cast(ptr, ctypes.py_object).value

    @create("()->Object")
    def __scope__():
        return context.frame[-1]

        # a way to print a scope nicely
            # to dict
            # tree print in code.*

        # scope/frame? flatten.
            # a func in code.scope
            # getattr setattr declare over a flat

            # maybe that's what a StackFrame is?
            # an object, assigned to various funcs/classes
            # you can declare directly in it, it has the getattr setattr code
    @create("()->Module")
    def __module__():
        for scope in reversed(context.frame):
            if context.extends(scope.__type__, context.scope_types.Module):
                return r@ scope
    @create("()->Env")
    def __env__():
        return context.scope.get_env()
    @create("()->List")
    @wraps(result=True)
    def __frame__():
        return context.frame # copy?
    @create("()->List")
    @wraps(result=True)
    def __stack__():
        return context.stack # copy?

    @create("(func_:Func, iter)->Iterable")
    def map(func_, iter): # *
        iter = context.unwrap_iter(context.operators.iter.native(iter))
        return context.obj.Object(context.basic_types.NativeIterator,
            __this__=builtins.map(lambda item: context.call(func_, ([item], {})), iter)
        )
    @create("(*iterables)->Iterable")
    def zip(*iterables):
        iterables = [context.unwrap_iter(context.operators.iter.native(iter)) for iter in iterables]
        return context.obj.Object(context.basic_types.NativeIterator,
            __this__=builtins.map(lambda group: w@ group, builtins.zip(*iterables))
        )
    @create("(iter, start:Int=0)->Iterable")
    @wraps("start")
    def enumerate(iter, start=0):
        iter = context.unwrap_iter(context.operators.iter.native(iter))
        return context.obj.Object(context.basic_types.NativeIterator,
            __this__=builtins.map(lambda group: w@ (w@ group[0], group[1]), builtins.enumerate(iter, start=start))
        )

# delim

# print, input (file vs ...!
# file can mean handle
# but also stream

# file = sys.stdout

# sep=' ', file=sys.stdout
# input([prompt])


# locals / scope
# super()
