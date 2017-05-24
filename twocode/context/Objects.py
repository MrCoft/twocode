from twocode import Utils

class Object(Utils.Object):
    def __init__(self, type=None, this=None):
        super().__init__()
        self.__type__ = type
        self.__bound__ = {}
        if this:
            self.__this__ = this
# actually, you cant register "items" ?

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

class Class(Object):
    def __init__(self, name=None):
        super().__init__()
        self.__fields__ = {}
        self.__parent__ = None
        self.__default__ = None
class BoundMethod(Object):
    def __init__(self, obj=None, func=None):
        super().__init__()
        self.args_pass()

# key -> var.value, on set and get
# a.b, a[b], in a: var x:T
# a func that sets it using a type
# a.__slots__ or __vars__ returns the original dict

# class wrappers
# this.

# class Scope:
#    var stack:List<Dict<String, Object>> = [{}]
# setattr for class - mirror getattr

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
# order

from twocode.context.Modules import Module
objects = [Func, Arg, Class, BoundMethod, Var, Module]
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
    for var, default in source().items():
        if var not in metafields:
            cls.__fields__[var] = Object(Class(), this=default) # unwrap
    source.__type__ = cls
    wrap_init(source)
for source in objects:
    source.__type__.__type__ = Class.__type__

def bind_context(context):
    from twocode.Repr import wrap_block, pack_args

    def class_getattr(obj, name):
        if name in obj.__fields__:
            return obj.__fields__[name]
        raise AttributeError()
    def class_repr(obj):
        fields = []
        fields_iter = sorted((context.unwrap_value(name), field) for name, field in obj.__fields__.items())
        for name, field in fields_iter:
            if not isinstance(field, Func):
                default_code = context.unwrap_value(context.builtins.repr.native(field))
                var_code = "var {}".format(name) + (" = " + default_code if field else "")
                fields.append(var_code)
        fields.append("")
        for name, field in fields_iter:
            if isinstance(field, Func):
                func_code = context.unwrap_value(context.builtins.repr.native(field))
                func_code = "func {}".format(name) + func_code[4:] #
                fields.append(name)
        block_code = "\n".join(fields)
        code = "class" + (" " + context.unwrap_value(obj.__name__) if obj.__name__ else "") + ":" + wrap_block(block_code)
        # name? func name?
        return code
    Class.__type__.__fields__["__getattr__"] = Func(native=class_getattr)
    Class.__type__.__fields__["__repr__"] = Func(native=class_repr, args=[Arg("this", type=Class)])
    # not passed to Int?

    def func_repr(obj):
        args = []
        for arg in obj.args:
            default_code = context.unwrap_value(context.builtins.repr.native(arg.default))
            arg_code = pack_args(arg.pack) + arg.name + (":{}".format(arg.type.__name__) if arg.type else "") + (" = {}".format(default_code) if arg.default else "")
            args.append(arg_code)
        block_code = context.unwrap_value(context.builtins.repr.native(obj.code))
        code = "func" + "({})".format(", ".join(args)) + ("->{}".format(obj.return_type.__name__) if obj.return_type else "") + ":" + wrap_block(block_code)
        return code
        # a func that prints a path to a type in the current context - full path if imported, else
    Func.__type__.__fields__["__repr__"] = Func(native=func_repr, args=[Arg("this", type=Func)])

def gen_node_classes(node_types):
    node_classes = {}
    for type_name, node_type in node_types.items():
        cls = Class
        cls.__name__ = type_name
        for var in node_types.vars:
            cls.__fields__[var.name] = Object(Class())
        node_classes[type_name] = cls
    return node_classes

# native - a macro func that ends up generating code with expressions
    # using other lang-specific code