from twocode import Utils
from twocode.context.Objects import *
import builtins

def gen_builtins(context):
    def native(code):
        nonlocal context
        builtins.exec(code)
    def eval(code):
        if type(code) is str:
            code = context.parse(code)
        else:
            code = context.unwrap_code(code)
        return context.eval(code)
    def parse(code):
        return context.parser.parse(code)
    def print(*objects):
        objects = [context.unwrap_value(context.convert(context.wrap_value(obj), context.builtins.String)) for obj in objects]
        builtins.print(*objects)
    # classes, builtins
    def repr(obj):
        obj = context.wrap_value(obj)
        if not "__repr__" in obj.__bound__:
            return "<path.A object at ID>"
        return context.call(obj.__bound__["__repr__"], ([], {}))

    __builtins__ = Utils.Object()
    for name, __native__ in Utils.redict(locals(), ["context"]).items():
        __builtins__[name] = Func(native=__native__)
    return __builtins__

# locals / scope
# open
# cd - virtual or not
# streams

# super()