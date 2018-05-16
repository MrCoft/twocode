from twocode import utils
import builtins
import textwrap
import ctypes

def add_builtins(context):
    wraps = context.native_wraps

    context.builtins = utils.Object()
    def create(signature):
        def wrap(func):
            f = context.obj.Func(native=func, sign=signature)
            context.builtins[func.__name__] = f
        return wrap

    # native-> null?
    # open -> FileStream
    @create("(code:String)->Object")
    @wraps("code")
    def native(code):
        # inspect
        # to a Object-wrapping python thingy.  Python.imp
        code = textwrap.dedent(code).strip()

        nonlocal context
        s, ret = [context.native_utils[name] for name in "scope, ret".split(", ")]

        builtins.exec(code, locals())
    context.native_utils = utils.Object()
    native_utils = context.native_utils
    class WrappedScope:
        def __getattr__(self, name):
            return context.unwrap(context.scope[name])
        def __setattr__(self, name, value):
            context.scope[name] = context.wrap(value)
    native_utils.scope = WrappedScope()
    def ret(obj):
        raise context.exc.Return(context.wrap(obj))
    native_utils.ret = ret
    # if the object was NOT wrapped and instead returned another object?
    # one that you could __call__? and it would do that

    @create('(*objects:Object, sep=" ", end="\\n", flush=true)')
    @wraps("sep", "end", "flush")
    def print(*objects, sep=" ", end="\n", flush=True):
        objects = [context.unwrap(context.operators.string.native(obj)) for obj in objects]
        builtins.print(*objects, sep=sep, end=end, flush=flush)

    # order from here

    @create("(module:Module)") # module path
    def reload(module):
        qualname = context.unwrap(context.operators.qualname.native(module))
        #if not qualname:
        #    return # exc
        env = context.scope.get_env()
        map = env.__qualnames__
        map.pop(id(module), None)
        builtins.print("qn", qualname)
        context.imp(qualname)
        # reuse the module object

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
        # [name]
        # getattr setattr declare? flat??
        pass
    @create("()->List")
    @wraps(result=True)
    def __frame__():
        return context.frame # copy?
    @create("()->Env")
    def __env__():
        return context.scope.get_env() # copy?
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
            __this__=builtins.map(lambda group: context.wrap(group), builtins.zip(*iterables))
        )
    @create("(iter, start:Int=0)->Iterable")
    @wraps("start")
    def enumerate(iter, start=0):
        iter = context.unwrap_iter(context.operators.iter.native(iter))
        return context.obj.Object(context.basic_types.NativeIterator,
            __this__=builtins.map(lambda group: context.wrap((context.wrap(group[0]), group[1])), builtins.enumerate(iter, start=start))
        )

# null -> here
# module -> append it
# stack -> replace it
# env -> replace it




# delim

# print, input (file vs ...!
# file can mean handle
# but also stream

# file = sys.stdout

# sep=' ', file=sys.stdout
# input([prompt])


# locals / scope
# super()
