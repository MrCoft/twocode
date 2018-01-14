from twocode import Utils

def add_typing(context):
    def convert(obj, type):
        if type.__type__ is context.objects.Func:
            return obj
            # exact same signature
        if type in context.inherit_chain(obj.__type__):
            return obj

        if obj.__type__ is context.basic_types.Null: # unwrap
            impl = context.impl(obj.__type__, "__default__")
            if impl:
                return context.call(impl, ([], {}))

        convert = context.impl(obj.__type__, "__to__")
        if convert:
            return context.call(convert, ([obj, type], {}))
        convert = context.impl(type, "__from__")
        if convert:
            return context.call(convert, ([obj], {}))

        raise context.exc.ConversionError()

    for name, instruction in Utils.redict(locals(), ["context"]).items():
        context.__dict__[name] = instruction

    class ConversionError(Exception):
        pass
    context.exc.ConversionError = ConversionError
