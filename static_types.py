from __future__ import annotations


# noinspection PyMethodParameters
class ContextTyping:
    def type_obj(c: Context):
        c.

    def convert(c, obj):
        pass

    def format(c, s: str):
        pass

class ContextCore:
    def eval(self, node):
        pass


# noinspection PyMethodParameters
class Context(
    ContextTyping, ContextCore
):
    def f(c):
        pass
