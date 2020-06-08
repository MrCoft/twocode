import twocode.context.new as _c


@type_check_decor(obj=context.obj.Ref)
def hasattr(obj, name):
    try:
        _c.getattr(obj, name, inline_exc=True)
        return True
    except InlineException:
        return False
