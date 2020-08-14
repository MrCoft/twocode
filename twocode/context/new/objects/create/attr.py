import twocode.context.new as _c


# noinspection PyPep8Naming
def Attr(type=None, default_=None):
    this = _c.objects.Object(_c.objects.types.Attr)
    this.type = dr@ type
    this.default_ = default_
    return this
