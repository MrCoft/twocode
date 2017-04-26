from twocode import Utils

class ConversionError(Exception):
    pass

def gen_typing(context):
    def convert(obj, type):
        if obj.__type__ == type:
            return obj

        try:
            convert = context.getattr(obj, "__to__")
        except AttributeError:
            convert = None
        if convert:
            return context.call(convert, ([obj, type], {}))

        try:
            convert = context.getattr(type, "__from__")
        except AttributeError:
            convert = None
        if convert:
            return context.call(convert, ([obj], {}))

        raise ConversionError()

    for name, instruction in Utils.redict(locals(), ["context"]).items():
        context.__dict__[name] = instruction