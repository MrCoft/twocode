import twocode.context.new as _c


# noinspection PyPep8Naming
def Arg(name=None, type=None, default_=None, pack=None, macro_=False):
    this = _c.objects.Object(_c.objects.types.Arg)
    this.name = name
    this.type = dr@ type
    this.default_ = default_
    this.pack = pack
    this.macro_ = macro_
    return this

