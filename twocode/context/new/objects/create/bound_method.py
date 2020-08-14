import twocode.context.new as _c


# noinspection PyPep8Naming
def BoundMethod(obj=None, func_=None):
    this = _c.objects.Object(_c.objects.types.BoundMethod)
    this.obj = dr@ obj
    this.func_ = dr@ func_
    return this
