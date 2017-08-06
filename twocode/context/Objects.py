from twocode import Utils
from twocode.Repr import wrap_block, pack_args
from twocode.context.Typing import gen_sign

# the wrapper func



# sign - requires basic types, probably objects and basics will patch that
# sign=

# doubt some methods here



# it seems right to make func.code internal

def add_objects(context):
    def hasattr(obj, name):
        try:
            context.getattr(obj, name)
            return True
        except AttributeError:
            return False
    def getattr(obj, name):
        try:
            return get_internals(obj, name)
        except AttributeError:
            pass
        type = obj.__type__
        if "__getattr__" in type.__fields__:
            try:
                return context.call(type.__fields__["__getattr__"], ((obj, name), {}))
            except AttributeError:
                pass
        fields = context.inherit_fields(type)
        if name in fields:
            attr = fields[name]
            if attr.__type__ is context.builtins.Var:
                return obj[name].value
            else:
                return context.obj.BoundMethod(obj, attr)
        raise AttributeError("{} object has no attribute {}".format("?", repr(name)))
    def setattr(obj, name, value):
        try:
            get_internals(obj, name)
            internal = True
        except AttributeError:
            internal = False
        if internal:
            set_internals(obj, name, value)
            return
        type = obj.__type__
        if "__setattr__" in type.__fields__:
            try:
                return context.call(type.__fields__["__setattr__"], ((obj, name, value), {}))
            except AttributeError:
                pass
        fields = context.inherit_fields(type)
        if name in fields:
            attr = fields[name]
            if attr.__type__ is context.builtins.Var:
                obj[name] = value
                return obj[name]
        raise AttributeError("{} object has no attribute {}".format("?", repr(name)))
        # name
    def get_internals(obj, name):
        if name == "__type__":
            return obj[name]
        if obj.__type__ is context.builtins.Type:
            if name == "__fields__":
                return None
                # returns an object whose writes work, a map
                # return wrapped(obj[name])
            if name == "__base__":
                return obj[name]
        if obj.__type__ is context.builtins.Func:
            if name == "code":
                return context.wrap_code(obj[name])
        if obj.__type__ is context.builtins.Arg:
            if name == "default":
                return context.wrap_code(obj[name])
        raise AttributeError()
    def set_internals(obj, name, value):
        if name == "__type__":
            raise AttributeError("can't set attribute {}".format(repr(name)))
        if obj.__type__ is context.builtins.Type:
            if name == "__fields__":
                raise AttributeError("can't set attribute {}".format(repr(name)))
            if name == "__base__":
                obj[name] = value
        if obj.__type__ is context.builtins.Func:
            if name == "code":
                obj[name] = context.unwrap_code(value)
        if obj.__type__ is context.builtins.Arg:
            if name == "default":
                obj[name] = context.unwrap_code(value)
    for name, instruction in Utils.redict(locals(), ["context"]).items():
        context.__dict__[name] = instruction

    context.obj = Utils.Object()
    class Object(Utils.Object):
        def __init__(self, type=None, this=None, **kwargs):
            super().__init__(**kwargs)
            self.__type__ = type
            if this is not None:
                self.__this__ = this
    context.obj.Object = Object
    # actually, you cant register "items"?

    def create(func):
        name = func.__name__
        def f(*args, **kwargs):
            type = context.builtins[name]
            obj = Object(type=type)
            func(obj, *args, **kwargs)
            return obj
        context.obj[name] = f
    sign_f = gen_sign(context)
    @create
    def Func(this, args=None, return_type=None, code=None, native=None, sign=None):
        if args is None: args = []
        this.scope = None
        this.args_pass()
        if sign:
            sign_f(this, sign)
        del this.sign
    @create
    def Arg(this, name="", type=None, default=None, pack=None, macro=False):
        this.args_pass()
    @create
    def Type(this):
        this.__fields__ = {}
        this.__base__ = None
    @create
    def BoundMethod(this, obj=None, func=None):
        this.args_pass()
    @create
    def Var(this, value=None, type_ref=None):
        this.args_pass()
    context.builtins.Type = None
    Type = context.obj.Type()
    Type.__type__ = Type
    context.builtins.Type = Type
    def gen_type(name):
        type = context.obj.Type()
        context.builtins[name] = type
        return type
    Func = gen_type("Func")
    Arg = gen_type("Arg")
    BoundMethod = gen_type("BoundMethod")
    Var = gen_type("Var")

    def attach(type, name):
        def wrap(func):
            type.__fields__[name] = context.obj.Func(native=func)
        return wrap
    @attach(Type, "__getattr__")
    def type_getattr(obj, name):
        #while obj:
        if name in obj.__fields__:
            return obj.__fields__[name]
        #    obj = obj.__base__
        raise AttributeError()
    @attach(Type, "__setattr__")
    def type_setattr(obj, name, value):
        if name in obj.__fields__:
            obj.__fields__[name] = value
            return
        raise AttributeError()
    @attach(Func, "__repr__")
    def func_repr(obj):
        args = []
        for arg in obj.args:
            default_code = repr(arg.default)
            # ":{}".format(arg.type.__name__) if arg.type else ""
            arg_code = pack_args(arg.pack) + ("macro " if arg.macro else "") + arg.name + ("") + (" = {}".format(default_code) if arg.default else "")
            args.append(arg_code)
        block_code = repr(obj.code)
        # if none? actual none

        # if native - @native

        # code = "func" + "({})".format(", ".join(args)) + ("->{}".format(obj.return_type.__name__) if obj.return_type else "") + ":" + wrap_block(block_code)


        # and maybe rethink internals. method cascade is enough of a reason


        code = "func" + "({})".format(", ".join(args)) + ":" + wrap_block(block_code)
        return code
    @attach(Type, "__repr__")
    def type_repr(obj):
        fields = []
        fields_iter = sorted((context.unwrap_value(name), field) for name, field in obj.__fields__.items())
        for name, field in fields_iter:
            if field.__type__ is context.builtins.Var:
                default_code = repr(field.value)
                # default_code = context.unwrap_value(context.convert(obj., context.builtins.String))
                var_code = "var {}".format(name) + (" = " + default_code if field.value else "")
                fields.append(var_code)
        fields.append("")
        for name, field in fields_iter:
            if field.__type__ is context.builtins.Func:
                func_code = context.unwrap_value(context.builtins.repr.native(field))
                # func_code = context.unwrap_value(context.convert(obj.code, context.builtins.String))
                # remove "this"
                func_code = "func {}".format(name) + func_code[4:] #
                fields.append(func_code)
        block_code = "\n".join(fields)
        code = "type:" + wrap_block(block_code)
        return code
    @attach(BoundMethod, "__repr__")
    def boundmethod_repr(obj):
        pass
# sort vars in repr?

def sign_objects(context):
    sign = gen_sign(context)
    Func, Arg, Type, BoundMethod, Var = [context.builtins[name] for name in "Func Arg Type BoundMethod Var".split()]
    sign(Type.__fields__["__getattr__"], "(this:Type, name:String)->Dynamic")
    sign(Type.__fields__["__setattr__"], "(this:Type, name:String, value:Dynamic)->Null")
    sign(Func.__fields__["__repr__"], "(this:Func)->String")
    sign(Type.__fields__["__repr__"], "(this:Type)->String")
    sign(BoundMethod.__fields__["__repr__"], "(this:Func)->String")

'''
for var_name, default in context.obj[name](Utils.Object()).items():
    var = Object()
    var.__type__ = Var
    var =
    type.__fields__[var_name] = Var()
    type.__fields__[var_name] = Object(Type(), this=default) # unwrap

# later register types?
'''

# native - a macro func that ends up generating code with expressions
    # using other lang-specific code