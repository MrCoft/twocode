
LOG = set()
LOG.add("DEBUG")

class Transpiler:
    def __init__(self):
        Transpiler.current = self
    current = None

    def search_module(self, module, scope):
        self.all_scopes = []
        self.all_types = []
        self.type_to_scope = {}
        for name in module.__this__:
            obj = module.__this__[name].value
            scope[name] = obj.__type__
            if obj.__type__ is Module:
                search_module(obj, Scope(name, parent=scope))
            if obj.__type__ is Class and obj not in builtins:
                self.all_types.append(obj)
                type_scope = Scope(name, parent=scope)
                self.type_to_scope[obj] = type_scope
        if "DEBUG" in LOG:

    def discover_classes(self):

    search_module(env, Scope())




builtins = call(env, "builtins").values()
# path = qualname(obj) - tree

print(*[op.qualname(type).split(".")[-1] for type in all_types], sep=", ")
# env tree
"""
Searching modules... found 6 classes
Searching modules... found 6 classes
Physics, Float2, Unit, Game, Map, ABC

print tree?

anim
+---Anim
async
    events

    old
    Event
    Log
    Relay

145 ast nodes


env tree:
Env tree:
|____Anim
| |____index

anim
anim.Anim
async.events.*
async.old.*
async.Event
async.Log
async.Relay

anim
anim.Anim
async.events.*
async.old.*
|____Event, Log, Relay


finished in 0.2 sec

"""

#