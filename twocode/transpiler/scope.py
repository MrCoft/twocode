class Scope:
    def __init__(self, desc=None, parent=None):
        self.vars = {}
        self.desc = desc
        self.parent = parent
        self.children = []
        if parent:
            parent.children.append(self)
        all_scopes.append(self)
    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True
    def __getitem__(self, key):
        return self.vars[key]
    def __setitem__(self, key, value):
        self.vars[key] = value
    def __repr__(self):
        return repr(self.vars)
    def full_desc(self):
        items = []
        scope = self
        while scope:
            if scope.desc:
                items.insert(0, scope.desc)
            scope = scope.parent
        return ".".join(items) if items else "<env>"
    def flatten(self):
        vars = {}
        scope = self
        while scope:
            for key, value in scope.vars.items():
                vars.setdefault(key, value)
            scope = scope.parent
        return vars
    def unique_name(self):
        vars = self.flatten()
        for i in range(16):
            name = "_{:x}".format(i)
            if name not in vars:
                return name
        import random
        ord = 2
        while True:
            for _ in range(4 ** ord):
                i = random.getrandbits(4 * ord)
                name = "_{{:0{}x}}".format(ord).format(i)
                if name not in vars:
                    return name
            ord += 1
