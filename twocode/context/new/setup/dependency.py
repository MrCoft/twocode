

class Dependency:
    def __init__(self, *, depends=None, inject=None):
        if depends is None:
            depends = []
        if isinstance(depends, str):
            depends = [depends]
        self.depends = depends
        self.inject = inject
setup_funcs = []
setup_scope = {}

def setup(*, depends=None, inject=None)
    def wrap(f):
        setup_funcs.append(Dependency(depends=depends, inject=inject))
        return f
    return wrap

def resolve(name):
    path = name.split('.')


def complete():
    global setup_funcs
    while setup_funcs:
        setup_funcs_re = []
        for obj in setup_funcs:
            pass

