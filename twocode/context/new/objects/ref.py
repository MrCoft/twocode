from twocode.utils.string import escape
import builtins
from twocode.context import new as _c


class Ref:
    def __init__(self, obj, type):
        self.__dict__['__refobj__'] = obj
        self.__dict__['__reftype__'] = type

    def __getattr__(self, name):
        return builtins.getattr(self.__dict__['__refobj__'], name)

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise Exception(f'can\'t set {escape(name)} of reference')
        builtins.setattr(self.__dict__['__refobj__'], name, value)

    def __repr__(self):
        return repr(self.__refobj__)

    @staticmethod
    def deref(ref):
        # REASON: lighter AttrRefs that allows None for internals
        if isinstance(ref, _c.obj.Ref):
            return ref.__refobj__
        return ref
