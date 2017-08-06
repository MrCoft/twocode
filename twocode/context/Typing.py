from twocode import Utils

class ConversionError(Exception):
    pass

def add_typing(context):
    def convert(obj, type):
        if obj.__type__ is type:
            return obj

        try:
            convert = context.getattr(obj, "__to__")
        except AttributeError:
            convert = None
        if convert:
            return context.call(convert, ((obj, type), {}))

        try:
            convert = context.getattr(type, "__from__")
        except AttributeError:
            convert = None
        if convert:
            return context.call(convert, ((obj,), {}))

        raise ConversionError()

    for name, instruction in Utils.redict(locals(), ["context"]).items():
        context.__dict__[name] = instruction

def gen_sign(context):
    def sign(func, signature):
        signature = "func{}: {{}}".format(signature)
        code = context.parser.parse(signature)
        node = code.lines[0].tuple.expr.func_def
        for arg in node.args:
            func_arg = context.obj.Arg()
            func_arg.name = arg.id
            # func_arg.type = arg.type type_id
            #if arg.value is not None:
            #    func_arg.default = context.wrap_code(arg.value)  - wrap
            func_arg.pack = arg.pack
            func_arg.macro = arg.macro
            func.args.append(func_arg)
        # custom tiny recursive eval
        # func.return_type = context.eval(node.return_type) # we cant eval type
    return sign