import twocode.context.new as _c
from twocode.context.new.setup import type_check_decor


@type_check_decor()  # obj=_c.obj.Ref)
def hasattr(obj, name):
    try:
        _c.objects.getattr(obj, name, inline_exc=True)
        return True
    except InlineException:
        return False

