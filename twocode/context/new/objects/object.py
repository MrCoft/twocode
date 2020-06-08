from twocode.context import new as _c


class Object:
    def __init__(self, __type__, **kwargs):
        self.__type__ = __type__
        self.__type_params__ = {}
        self.__dict__.update(kwargs)

    def __repr__(self):
        return _c.safe_repr(self)
