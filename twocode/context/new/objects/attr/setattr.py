from twocode.context.new.setup import type_check_decor


# @inline_exc(AttributeError)
@type_check_decor()  # obj=context.obj.Ref)
def setattr(obj, name, value):
    try:
        get_internals(obj, name, inline_exc=True)
        internal = True
    except InlineException:
        internal = False
    if internal:
        set_internals(obj, name, value)
        return
    # this pattern?
    fields = context.inherit_fields(obj.__type__)
    if name in fields:
        attr = fields[name]
        type_check(attr, context.obj.Ref.Object)
        if attr.__type__ is context.objects.Attr:
            builtins.setattr(obj, name, value.__refobj__)
            return
            # __mov__?
        raise InlineException("can't set attribute {} of {}".format(escape(name), op.qualname(obj.__type__)))
    if "__setattr__" in fields:
        try:
            return context.call(r(context.objects.Func)@ fields["__setattr__"], ([obj, name, value], {})) # , inline_exc=True
        except AttributeError:
            pass
    raise InlineException("{} object has no attribute {}".format(op.qualname(obj.__type__)), escape(name))
