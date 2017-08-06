from twocode.context.Typing import gen_sign
import builtins

# c - context.scope.a
# ret() - raises exc

# scope gives access to builtins, exc, basic types

def add_builtins(context):
    sign = gen_sign(context)
    def create(signature):
        def wrap(func):
            f = context.obj.Func(native=func)
            sign(f, signature)
            context.builtins[func.__name__] = f
        return wrap

    # native-> null?
    # open -> FileStream
    @create("(code:String)->Dynamic")
    def native(code):
        nonlocal context
        builtins.exec(code)
    @create("(obj:Dynamic)->String")
    def repr(obj):
        obj = context.wrap_value(obj)
        builtins.print(type(obj.__type__))
        try: #
            repr = context.getattr(obj, "__repr__")
        except AttributeError:
            return "<path.A object at id>"
        return context.call(repr, ((), {}))
    @create("(*objects:Dynamic)->Null")
    def print(*objects, end="\n", flush=True):
        objects = [context.unwrap_value(context.convert(context.wrap_value(obj), context.builtins.String)) for obj in objects]
        builtins.print(*objects, flush=flush)
    @create('(file:String, mode:String="r", encoding:String="utf-8")->Dynamic')
    def open(file, mode="r", encoding="utf-8"):
        return builtins.open(file, mode=mode, encoding=encoding)
    @create("(code:String, scope=null, file:String=null)->Dynamic")
    def eval(code=None, scope=None, file=None):
        # swap_stack
        if file:
            code = builtins.open(file, encoding="utf-8").read()
            # __file__
        if type(code) is str:
            code = context.parse(code)
        else:
            code = context.unwrap_code(code)
        return context.eval(code)
    # scope_stack

# eval
# new / append

# null -> here
# module -> in it
# stack -> in it, isolated
    # conversions assume isolated

    # share_scope





# [scope] translates to stack?

# this = always a term-stack above [top object, scope stack]
# scope1 + scope2, +=


# delim

# print, input (file vs ...!
# file can mean handle
# but also stream

# file = sys.stdout

# sep=' ', file=sys.stdout
# input([prompt])


# locals / scope
# super()