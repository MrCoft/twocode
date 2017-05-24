import os
from twocode.context.Objects import Object

# eval along the way
# sources
# its just a recursive scope
# correct execution stack while inside
# copy-able
# import as

class Module(Object):
    def __init__(self, path=None):
        path = os.path.abspath(path) if path else None
        super().__init__()
        self.scope = {}
        self.__path__ = path
    # .M, .p

# explicit path loads a chain of these, returns the thing at the end
# end with a .T attempts to set it to T.T, or returns that - nat crossroad

# relative, doesnt have to be a package, priority


# always in scope of module stack
# new console - new empty module - <input>


def gen_modules(context):
    context.modules = {}

    def imp(node):
        for path in node.imports:
            filepath = "/".join(path.path)
            for source in context.sources:
                filename = os.path.join(source, filepath) + ".2c"
                if os.path.exists(filename):
                    context.load(filename)
                    return
            raise ImportError("no module named {}".format(repr(path.path[0]))) #

    context.imp = imp