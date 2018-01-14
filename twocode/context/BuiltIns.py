from twocode import Utils
import builtins
import textwrap
import ctypes

def add_builtins(context):
    wraps = context.native_wraps

    context.builtins = Utils.Object()
    def create(signature):
        def wrap(func):
            f = context.obj.Func(native=func, sign=signature)
            context.builtins[func.__name__] = f
        return wrap

    # native-> null?
    # open -> FileStream
    @create("(code:String)->Dynamic")
    @wraps("code")
    def native(code):
        # inspect
        # scope -> ns, _s? ns.a = unwrap(scope[a])
        # to a Dynamic-wrapping python thingy.  Python.imp
        code = textwrap.dedent(code).strip()

        nonlocal context
        s = context.Wrapper(context.scope)
        def ret(obj):
            raise context.exc.Return(context.wrap(obj))

        builtins.exec(code, locals())

    @create('(*objects:Dynamic, sep=" ", end="\\n", flush=true)')
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

    @create('(file:String, mode="r", encoding="utf-8")->Dynamic')
    @wraps("file", "mode", "encoding")
    def open(file, mode="r", encoding="utf-8"):
        return builtins.open(file, mode=mode, encoding=encoding)
    @create("(code:String, scope=null, ?file:String)->Dynamic")
    @wraps("code", "scope", "file")
    def eval(code=None, scope=None, file=None):
        # swap_stack
        if file:
            code = builtins.open(file, encoding="utf-8").read()
            context.declare(scope, "__file__", context.wrap(file))
        if type(code) is str:
            code = context.parse(code)
        else:
            code = context.unwrap_code(code)
        if scope:
            try:
                scope = context.convert(scope, context.scope_types.Scope)
            except context.exc.ConversionError:
                scope = context.obj.Object(context.scope_types.ObjectScope, object=scope)
            frame = [context.scope.get_env(), scope]
            with context.FrameContext(frame):
                return context.eval(code)
        else:
            return context.eval(code)
    @create("(code:String, ?file:String)->Code")
    @wraps("code", "file")
    def parse(code=None, file=None):
        if file:
            code = builtins.open(file, encoding="utf-8").read()
        return context.wrap_code(context.parse(code))

    @create("(obj:Dynamic)->Int")
    @wraps(wrap_return=True)
    def addressof(obj):
        return ctypes.addressof(obj)
    @create("(ptr:Int, type:Class)->Dynamic")
    @wraps("ptr")
    def deref(ptr, type):
        return ctypes.cast(ptr, ctypes.py_object).value

    @create("()->Dynamic")
    def __scope__():
        # [name]
        # getattr setattr declare? flat??
        pass
    @create("()->List")
    @wraps(wrap_return=True)
    def __frame__():
        return context.frame # copy?
    @create("()->Env")
    def __env__():
        return context.scope.get_env() # copy?
    @create("()->List")
    @wraps(wrap_return=True)
    def __stack__():
        return context.stack # copy?

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