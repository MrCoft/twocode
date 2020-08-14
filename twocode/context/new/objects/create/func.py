import twocode.context.new as _c


# noinspection PyPep8Naming
def Func(args=None, return_type=None, code=None, native=None, sign=None):
    this = _c.objects.Object(_c.objects.types.Func)
    if args is None: args = []
    this.frame = None
    this.args = args
    this.return_type = dr@ return_type
    this.code = code
    this.native = native
    if sign:
        _c.setup.sign(this, sign)
    return this
