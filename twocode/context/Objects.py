from twocode import Utils

class Object(Utils.Object):
    def __init__(self, type=None, this=None):
        super().__init__()
        self.__type__ = type
        self.__bound__ = {}
        if this:
            self.__this__ = this

class Func(Object):
    def __init__(self, args=None, return_type=None, code=None, native=None):
        if args is None: args = []
        super().__init__()
        self.scope = None
        self.args_pass()
class Arg(Object):
    def __init__(self, name="", type=None, default=None, pack=None):
        super().__init__()
        self.args_pass()
class BoundMethod(Object):
    def __init__(self, obj=None, func=None):
        super().__init__()
        self.args_pass()

class Class(Object):
    def __init__(self, name=None):
        super().__init__()
        self.__name__ = name
        self.__fields__ = {}
        self.__parent__ = None
        self.__default__ = None

# has to be runtime
# class Scope:
#    var stack:List<Dict<String, Object>> = [{}]
# loading packages how? some command or something about the content that makes it order independent

class Var(Object):
    def __init__(self, value=None, type=None):
        super().__init__()
        self.args_pass()
# retype on redeclare
# check on assignment, but treat it as what it is
# default
# nullable

# native
class Scope:
    def __init__(self):
        self.stack = [{}]
    def __contains__(self, name):
        for dict in reversed(self.stack):
            if name in dict:
                return True
        return False
    def __getitem__(self, name):
        for dict in reversed(self.stack):
            if name in dict:
                return dict[name]
        raise NameError("name {} is not defined".format(repr(name)))
    def __setitem__(self, name, obj):
        for dict in reversed(self.stack):
            if name in dict:
                dict[name] = obj
                return
        raise NameError("name {} is not defined".format(repr(name)))
    def copy(self):
        scope = Scope()
        scope.stack = self.stack.copy()
        return scope

class Return(Exception):
    def __init__(self, value=None):
        self.value = value

objects = [Func, Arg, BoundMethod, Class, Var]
def wrap_init(source):
    init_f = source.__init__
    def wrapped(self, *args, **kwargs):
        init_f(self, *args, **kwargs)
        # bind
        try:
            self.__bound__["__repr__"] = BoundMethod(self, source.__type__.__fields__["__repr__"])
        except: pass
        self.__type__ = source.__type__
    source.__init__ = wrapped
metafields = Object().keys()
for source in objects:
    name = source.__name__
    cls = Class()
    cls.__name__ = name
    for var, default in source().items():
        if var not in metafields:
            cls.__fields__[var] = Object(Class(), this=default) # unwrap
    source.__type__ = cls
    wrap_init(source)
for source in objects:
    source.__type__.__type__ = Class.__type__

def class_getattr(obj, name):
    if name in obj.__fields__:
        return obj.__fields__[name]
    raise AttributeError()
Class.__type__.__fields__["__getattr__"] = Func(native=class_getattr)
def func_repr(this):
    #this = context.scope['__this__']
    return "f"
    return repr(obj.code)
Func.__type__.__fields__["__repr__"] = Func(native=func_repr)
# Class.__repr__ = lambda self: self.__name__
# Class.__type__.__fields__["__getattr__"] = Func(native=lambda obj, attr: obj.__fields__[attr])

# context object - do not modify methods! but start an appropriate scope for them

def gen_node_classes(node_types):
    node_classes = {}
    for type_name, node_type in node_types.items():
        cls = Class
        cls.__name__ = type_name
        for var in node_types.vars:
            cls.__fields__[var.name] = Object(Class())
        node_classes[type_name] = cls
    return node_classes

# an object instance
# class is its class, parent chain
# or its class is Object whose class is Class?

# native - a macro func that ends up generating code with expressions
    # using other lang-specific code

# objects... are linked, how, for it to work best?
# NO NATIVE OUTSDIE BUILTIN