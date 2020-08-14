import twocode.context.new as _c
from twocode.context.new.setup import type_check_decor


# @inline_exc(AttributeError)
@type_check_decor()  # obj=context.obj.Ref)
def getattr(obj, name: str):
    """
        returns wrapped value
    """
    try:
        return _c.objects.get_internals(obj, name, inline_exc=True)
    except InlineException:
        pass
    fields = context.inherit_fields(obj.__type__)
    if name in fields:
        # check if extends, complex behavior, care about it being an Object only!
        attr = fields[name]
        type_check(attr, context.obj.Ref.Object)
        if attr.__type__ is context.objects.Attr:
            return r(attr.__type__)@ builtins.getattr(obj, name)
        try:
            context.callable(r(attr.__type__)@ attr, ([], {}), inline_exc=True)
        except InlineException:
            # if not static, and we throw exc otherwise! can't leave existing attr to __getattr__
            pass
        else:
            return r(context.objects.BoundMethod)@ context.obj.BoundMethod(obj, attr)
    if "__getattr__" in fields:
        try: # is func?
            return context.call(r(context.objects.Func)@ fields["__getattr__"], ([obj, name], {})) # , inline_exc=True
        except AttributeError:
            pass
    raise InlineException("{} object has no attribute {}".format(uw@ context.call_method(context.AttrRefs(obj).__type__, "source"), escape(name)))
    raise InlineException("{} object has no attribute {}".format(op.qualname(obj.__type__)), escape(name))
