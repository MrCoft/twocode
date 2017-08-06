from twocode import Utils
import os

def add_scope(context):
    def declare(name, value, type=None):
        if type is None: type = context.builtins.Dynamic
        scope = context.stack[-1]
        if scope.__type__ is Scope:
            scope.__this__[name] = context.obj.Var(value, type)
        else:
            scope[name] = value
    def swap_stack(scope):
        if scope is None: scope = ScopeStack() # weird. also builtins into normal one?
        old_scope = context.scope
        context.scope = scope
        context.stack = scope.__this__
        return old_scope
    for name, instruction in Utils.redict(locals(), ["context"]).items():
        context.__dict__[name] = instruction

    def gen_type(name):
        type = context.obj.Type()
        context.builtins[name] = type
        return type
    Scope = gen_type("Scope")
    Scope.__base__ = context.builtins.Map
    ScopeStack = gen_type("ScopeStack")
    ScopeStack.__base__ = context.builtins.List
    Module = gen_type("Module")
    Module.__base__ = Scope

    def attach(type, name):
        def wrap(func):
            type.__fields__[name] = context.obj.Func(native=func)
        return wrap
    # getattr
    @attach(Scope, "__init__")
    def scope_init(this, map=None):
        if map is None: map = {}
        this.__this__ = map #? __map__ ? base
    @attach(Scope, "__setitem__")
    def scope_setitem(this, name, value):
        this.__this__[name].value = value
    @attach(Scope, "__add__")
    def scope_add(this, scope):
        pass
    def module_init(this, path=None, file=None, uproot=False):
        scope_init(this)
        this.__path__ = path
        this.__file__ = os.path.abspath(file) if file else None
        this.__root__ = {} if uproot else None
    @attach(Module, "__getitem__")
    def module_getitem(this, name):
        pass
        # thing has data, lookup jump it
        # submodules from path
    @attach(Module, "__setitem__")
    def module_setitem(this, name, value):
        if value.__type__ is context.builtins.Module:
            pass # assign to root
    @attach(Module, "__getattr__")
    def module_getattr(this, name):
        if name in this:
            return this[name]
        raise AttributeError()
    # args=[Arg("this"), Arg("name")])
    @attach(Module, "__setattr__")
    def module_setattr(this, name, value):
        return module_setitem()
        if name in this:
            this[name] = value
            return
        raise AttributeError()
    # args=[Arg("this"), Arg("name"), Arg("value")])


    # builtins bound to root look-up
# builtins, basic types
# self.sources = []
# -> native types? native.types

    #codebase = os.path.join(os.path.dirname(os.path.dirname(__file__)), "code")
    #context.sources.append(codebase)

    def lookup(path):
        filepath = os.path.sep.join(path.split("."))
        for source in context.sources:
            if isinstance(source, str):
                filename = os.path.join(source, filepath)
                if os.path.exists(filename):
                    return filename
                if os.path.exists(filename + ".2c"):
                    return filename + ".2c"
            else:
                pass #
                # parse func
                # zip, native python
        # first term, not path
        # bound to path - redirect works

    class ScopeStack:
        def __init__(self):
            root = context.new(Module)
            root.name = context.wrap_value("<module>")
            self.__this__ = [root]
        def __contains__(self, name):
            for scope in reversed(self.__this__):
                if name in scope:
                    return True
            if name in context.builtins:
                return True
            return False
        def __getitem__(self, name):
            for scope in reversed(self.__this__):
                if name in scope:
                    return scope[name]
            if name in context.builtins:
                return context.builtins[name]
            if name in context.builtins.NodeTypes:
                return context.builtins.NodeTypes[name]
            path = lookup(name)
            # if path:
            #     return context.imp()
            # reach root
            # sources (fake if same name) - elsewhere too?
            # root -> sources -> thing
            raise NameError("name {} is not defined".format(repr(name)))
        def __setitem__(self, name, value):
            for scope in reversed(self.__this__):
                if name in scope:
                    scope[name] = value
                    return
            raise NameError("name {} is not defined".format(repr(name)))
        def copy(self):
            scope_stack = ScopeStack()
            scope_stack.__this__ = self.__this__.copy()
            return scope_stack

    context.scope = ScopeStack()
    context.stack = context.scope.__this__