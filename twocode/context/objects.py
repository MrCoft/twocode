from twocode import utils
from twocode.lang.repr import wrap_block, pack_args
from twocode.utils.code import inline_exc, InlineException
import inspect
import functools
import builtins
from twocode.utils.string import escape

# automatic python object

# fail qualname?
# an ensure is not null or error func?
    #  at func_repr
# is this how i call funcs?
    # repr_bound in class_repr

def add_objects(context):
    def hasattr(obj, name):
        try:
            context.getattr(obj, name, inline_exc=True)
            return True
        except InlineException:
            return False
    @inline_exc(AttributeError)
    def getattr(obj, name):
        """
            returns wrapped value
        """
        try:
            return get_internals(obj, name, inline_exc=True)
        except InlineException:
            pass
        fields = context.inherit_fields(obj.__type__)
        if "__getattr__" in fields:
            try:
                return context.call(fields["__getattr__"], ([obj, name], {})) # , inline_exc=True
            except AttributeError:
                pass
        if name in fields:
            attr = fields[name]
            if attr.__type__ is context.objects.Attr:
                return builtins.getattr(obj, name)
            try:
                context.callable(attr, ([], {}), inline_exc=True)
            except InlineException:
                pass
            else:
                return context.obj.BoundMethod(obj, attr)
        raise InlineException("{} object has no attribute {}".format(context.unwrap(context.operators.qualname.native(obj.__type__)), escape(name)))
    @inline_exc(AttributeError)
    def setattr(obj, name, value):
        try:
            get_internals(obj, name, inline_exc=True)
            internal = True
        except InlineException:
            internal = False
        if internal:
            set_internals(obj, name, value)
            return
        # this pattern?
        fields = context.inherit_fields(obj.__type__)
        if "__setattr__" in fields:
            try:
                return context.call(fields["__setattr__"], ([obj, name, value], {})) # , inline_exc=True
            except AttributeError:
                pass
        if name in fields:
            attr = fields[name]
            if attr.__type__ is context.objects.Attr:
                builtins.setattr(obj, name, value)
                return
            raise InlineException("can't set attribute {} of {}".format(escape(name), context.unwrap(context.operators.qualname.native(obj.__type__))))
        raise InlineException("{} object has no attribute {}".format(context.unwrap(context.operators.qualname.native(obj.__type__)), escape(name)))
    @inline_exc(AttributeError)
    def get_internals(obj, name):
        """
            attributes directly accessible from within the runtime are clunky to work with from python
                .name = "func" becomes .name = Object(__type__=String, __this__="func")
            some are so common that the constant wrapping and unwrapping would have a horrible effect on performance
            it's also very easy for some to cause a loop
                e.g. the deprecated __bound__ would keep creating BoundMethods of BoundMethods

            internals are simple, unwrapped attributes of core types
            they cannot be referenced but you can get and set a copy

            NOTE:
            class-typed attributes are internal if their unset value is an unwrapped None
        """
        if name == "__type__":
            return obj.__type__
        if obj.__type__ is context.objects.Func:
            if name == "code":
                """
                    code execution is common

                    one option is to make f.code get a wrapper over the python tree
                    it would be able to travel the tree by producing more wrappers on demand
                    generated code objects would have to be wrappers too
                    i don't think live editing is important
                """
                # change to wrapped at some point
                return context.wrap_code(obj.code)
            if name == "args":
                return context.wrap(obj.args)
            if name == "native":
                return obj if obj.native else context.wrap(None)
            if name == "frame":
                return context.wrap(obj.frame) # should be stack frame, or... why not just a list of scopes?
        if obj.__type__ is context.objects.Arg:
            if name == "name":
                return context.wrap(obj.name)
            if name == "type":
                return context.wrap(obj.type)
            if name == "default_":
                return context.wrap_code(obj.default_)
            if name == "pack":
                return context.wrap_code(obj.pack)
            if name == "macro_":
                return context.wrap(obj.macro_)
        if obj.__type__ is context.objects.Class:
            if name == "__fields__":
                return context.wrap(obj.__fields__)
            if name == "__base__":
                return context.wrap(obj.__base__)
            if name == "__frame__":
                return context.wrap(obj.__frame__)
        if obj.__type__ is context.objects.Attr:
            if name == "type":
                return context.wrap(obj.type)
            if name == "default_":
                return context.wrap_code(obj.default_)
        if obj.__type__ is context.objects.Var:
            if name == "value":
                return context.wrap_code(obj.value)
            if name == "type":
                return context.wrap(obj.type)
        raise InlineException()
    @inline_exc(AttributeError)
    def set_internals(obj, name, value):
        if name == "__type__":
            raise InlineException("can't set attribute {} of {}".format(escape(name)))
        if obj.__type__ is context.objects.Func:
            if name == "code":
                obj.code = context.unwrap_code(value)
            if name == "args":
                obj.args = context.unwrap(value)
            if name == "native":
                raise InlineException("can't set attribute {} of {}".format(escape(name)))
            if name == "frame":
                obj.frame = context.unwrap(value)
        if obj.__type__ is context.objects.Arg:
            if name == "name":
                obj.name = context.unwrap(value)
            if name == "type":
                obj.type = context.unwrap(value)
            if name == "default_":
                obj.default_ = context.unwrap_code(value)
            if name == "pack":
                obj.pack = context.unwrap_code(value)
            if name == "macro_":
                obj.macro_ = context.unwrap(value)
        if obj.__type__ is context.objects.Class:
            if name == "__fields__":
                obj.__fields__ = context.unwrap(value)
            if name == "__base__":
                obj.__base__ = context.unwrap(value)
            if name == "__frame__":
                obj.__frame__ = context.unwrap(value)
        if obj.__type__ is context.objects.Attr:
            if name == "type":
                obj.type = context.unwrap(value)
            if name == "default_":
                obj.default_ = context.unwrap_code(value)
        if obj.__type__ is context.objects.Var:
            if name == "value":
                obj.value = context.unwrap_code(value)
            if name == "type":
                obj.type = context.unwrap(value)
    for name, instruction in utils.redict(locals(), "context".split()).items():
        context.__dict__[name] = instruction

    def wraps(*names, result=False):
        def wrap(f):
            sign = inspect.signature(f)
            sign = list(sign.parameters.values())
            indices = []
            keywords = set()
            wrap_args = None
            wrap_kwargs = False
            arg_names = set()
            for i, param in enumerate(sign):
                if param.name in names:
                    if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                        indices.append(i)
                        keywords.add(param.name)
                    if param.kind == inspect.Parameter.KEYWORD_ONLY:
                        keywords.add(param.name)
                    if param.kind == inspect.Parameter.VAR_POSITIONAL:
                        wrap_args = i
                    if param.kind == inspect.Parameter.VAR_KEYWORD:
                        wrap_kwargs = True
                if param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                    arg_names.add(param.name)
            @functools.wraps(f)
            def wrapped(*args, **kwargs):
                args = list(args)
                for index in indices:
                    if len(args) > index:
                        args[index] = context.unwrap(args[index])
                for name in keywords:
                    if name in kwargs:
                        kwargs[name] = context.unwrap(kwargs[name])
                if wrap_args is not None:
                    args[wrap_args:] = (context.unwrap(item) for item in args[wrap_args:])
                if wrap_kwargs:
                    for name in kwargs:
                        if name not in arg_names:
                            kwargs[name] = context.unwrap(kwargs[name])
                return_value = f(*args, **kwargs)
                if result:
                    return_value = context.wrap(return_value)
                return return_value
            return wrapped
        return wrap
    context.native_wraps = wraps

    context.obj = utils.Object()
    class Object:
        def __init__(self, __type__, **kwargs):
            self.__type__ = __type__
            self.__type_params__ = None
            self.__dict__.update(kwargs)
        def __repr__(self):
            return context.unwrap(context.operators.repr.native(self))
            return context.object_repr(self)
    context.obj.Object = Object
    class Ref:
        def __init__(self, obj, type):
            self.obj = obj
            self.type = type
    context.obj.Ref = Ref

    def create(func):
        name = func.__name__
        def f(*args, **kwargs):
            type = context.objects[name]
            obj = Object(type)
            func(obj, *args, **kwargs)
            return obj
        context.obj[name] = f
    @create
    def Func(this, args=None, return_type=None, code=None, native=None, sign=None):
        if args is None: args = []
        this.frame = None
        # OPTIM: pass_args
        this.args = args
        this.return_type = return_type
        this.code = code
        this.native = native
        if sign:
            context.setup.sign(this, sign)
    @create
    def Arg(this, name=None, type=None, default_=None, pack=None, macro_=False):
        this.name = name
        this.type = type
        this.default_ = default_
        this.pack = pack
        this.macro_ = macro_
    @create
    def Class(this):
        this.__fields__ = {}
        this.__base__ = None
        this.__frame__ = None
    @create
    def Attr(this, type=None, default_=None):
        this.type = type
        this.default_ = default_
    @create
    def BoundMethod(this, obj=None, func_=None):
        this.obj = obj
        this.func_ = func_
    @create
    def Var(this, value=None, type=None):
        this.value = value
        this.type = type

    context.objects = utils.Object()
    context.objects.Class = None
    Class = context.obj.Class()
    Class.__type__ = Class
    context.objects.Class = Class
    def gen_type(name):
        type = context.obj.Class()
        context.objects[name] = type
        return type
    Func = gen_type("Func")
    Arg = gen_type("Arg")
    Attr = gen_type("Attr")
    BoundMethod = gen_type("BoundMethod")
    Var = gen_type("Var")

    add_vars = context.setup.add_vars

    # internals are set to wrapped null when constructed
    # class fields to {}
    add_vars(Func, """
        var args:List<Arg> = []
        var return_type:Class
        var code:Code
        var native:Func
        var frame:StackFrame
    """)
    add_vars(Arg, """
        var name:String
        var type:Class
        var default_:Code
        var pack
        var macro_:Bool = false
    """)
    add_vars(Class, """
        var __fields__:Map<String,Object> = []
        var __base__:Class
        var __frame__:StackFrame
    """)
    add_vars(Attr, """
        var type:Class
        var default_:Code
    """)
    add_vars(BoundMethod, """
        var obj:Object
        var func_:Func
    """)
    add_vars(Var, """
        var value:Object
        var type:Class
    """)

    def attach(type, name, **kwargs):
        def wrap(func):
            type.__fields__[name] = context.obj.Func(native=func, **kwargs)
        return wrap

    @attach(Func, "__init__", sign="(this:Func, ?args:List<Arg>, ?return_type:Class, ?code:Code, ?sign:String)")
    @wraps("args", "sign")
    def func_init(this, args=None, return_type=None, code=None, sign=None):
        if args is None: args = []
        this.args = args
        this.return_type = context.unwrap(return_type)
        this.code = context.unwrap_code(code)
        this.native = None
        this.frame = None
        if sign:
            if this.args or this.return_type:
                raise ValueError("got multiple signatures")
            sign = "func{}: {{}}".format(sign)
            func_obj = context.eval(context.parse(sign), type="expr")
            this.args = func_obj.args
            this.return_type = func_obj.return_type
            # transplant scope?
            # or even use current one, for construction?

            # __scope__
            # __stack__
            # __frame__
    @attach(Arg, "__init__", sign='(this:Arg, name:String, ?type:Class, ?default_:Code, pack:String="", macro_:Bool=false)')
    @wraps("name", "pack", "macro_")
    def arg_init(this, name, type=None, default_=None, pack="", macro_=False):
        this.name = name
        this.type = context.unwrap(type)
        this.default_ = context.unwrap_code(default_)
        this.pack = pack
        this.macro_ = macro_
    @attach(Class, "__init__", sign="(this:Class)")
    def class_init(this):
        this.__fields__ = {}
        this.__base__ = None
        this.__frame__ = None
    @attach(Attr, "__init__", sign="(this:Attr, ?type:Class, ?default_:Code)")
    def attr_init(this, type=None, default_=None):
        this.type = context.unwrap(type)
        this.default_ = context.unwrap_code(default_)
    @attach(BoundMethod, "__init__", sign="(this:BoundMethod, obj:Object, func_:Func)")
    def boundmethod_init(this, obj, func_):
        this.obj = obj
        this.func_ = func_
    @attach(Var, "__init__", sign="(this:Var, ?value:Object, ?type:Class)")
    def var_init(this, value=None, type=None):
        this.value = context.unwrap(value)
        this.type = context.unwrap(type)

    @attach(Class, "__getattr__", sign="(this:Class, name:String)->Object")
    @wraps("name")
    @inline_exc(AttributeError)
    def class_getattr(this, name):
        fields = this.__fields__
        if name in fields:
            attr = fields[name]
            try:
                context.callable(attr, ([], {}), inline_exc=True)
            except InlineException:
                pass
            else:
                return attr
        raise InlineException()
    @attach(Class, "__setattr__", sign="(this:Class, name:String, value:Object)->Null")
    @wraps("name")
    @inline_exc(AttributeError)
    def class_setattr(this, name, value):
        if name in this.__fields__:
            this.__fields__[name] = value
            return
        raise InlineException()
    @attach(Func, "signature", sign="(f:Func, ?type:Class)->String")
    @wraps("type", result=True)
    def func_signature(f, type=None):
        bound = type and context.bound(f, type)
        args = []
        for arg in f.args if not bound else f.args[1:]:
            if not arg.name:
                raise ValueError("unnamed argument")
            arg_code =\
                pack_args(arg.pack) +\
                ("macro " if arg.macro_ else "") +\
                arg.name +\
                (":{}".format(context.unwrap(context.operators.qualname.native(arg.type))) if arg.type else "") +\
                ("={}".format(str(arg.default_)) if arg.default_ else "")
            args.append(arg_code)
        code =\
            "({})".format(", ".join(args)) +\
            ("->{}".format(context.unwrap(context.operators.qualname.native(f.return_type))) if f.return_type else "")
        return code
    @attach(Func, "source_bound", sign="(f:Func, ?type:Class, ?name:String)->String")
    @wraps("type", "name", result=True)
    def func_source_bound(f, type=None, name=None):
        static = type and not context.bound(f, type)
        signature = context.unwrap(context.call_method(f, "signature", type))
        block_code = repr(f.code) if f.code is not None else "{}"
        # print line splitting is wrong (inside token)
        code =\
            ("@static " if static else "") +\
            ("@Func.native(ptr={}) ".format(format(id(f.native), "#x")) if f.native else "") +\
            "func" +\
            (" " + name if name else "") +\
            signature +\
            ":" +\
            wrap_block(block_code)
        return code
    @attach(Func, "source", sign="(f:Func)->String")
    @wraps(result=True)
    def func_source(f):
        return context.call_method(f, "source_bound")
    @attach(Func, "type", sign="(f:Func, ?type:Class)->String")
    @wraps("type", result=True)
    def func_type(f, type=None):
        bound = type and context.bound(f, type)
        args = []
        for arg in f.args if not bound else f.args[1:]:
            arg_code =\
                pack_args(arg.pack) +\
                ("?" if arg.default_ else "") +\
                (context.unwrap(context.operators.qualname.native(arg.type)) if arg.type else "()")
            args.append(arg_code)
        code =\
            (("({})").format(",".join(args)) if len(args) != 1 else args[0]) +\
            "->" +\
            (context.unwrap(context.operators.qualname.native(f.return_type)) if f.return_type else "()")
        return code
    @attach(Func, "repr", sign="(f:Func)->String")
    @wraps(result=True)
    def func_repr(f):
        return "<func {}>".format(context.unwrap(context.call_method(f, "type")))
    @attach(Arg, "repr", sign="(this:Arg)->String")
    @wraps(result=True)
    def arg_repr(this):
        buf = []
        buf.append(context.unwrap(context.operators.repr.native(context.wrap(this.name))))
        if this.type:
            buf.append(context.unwrap(context.operators.qualname.native(this.type)))
        if this.default_ is not None:
            buf.append("default_={}".format(repr(this.default_)))
        if this.pack:
            buf.append("pack={}".format(context.unwrap(context.operators.repr.native(context.wrap(this.type)))))
        if this.macro_:
            buf.append("macro_={}".format(context.unwrap(context.operators.repr.native(context.wrap(this.macro_)))))
        return "Arg({})".format(", ".join(buf))
    @attach(Class, "source", sign="(type:Class)->String")
    @wraps(result=True)
    def class_source(type):
        # @internal - for certain vars
        fields = []
        fields_iter = sorted((context.unwrap(name), field) for name, field in type.__fields__.items())
        for name, field in fields_iter:
            if field.__type__ is context.objects.Attr:
                default_code = repr(field.default_)
                var_code =\
                    "var {}".format(name) +\
                    (":{}".format(context.unwrap(context.operators.qualname.native(field.type))) if field.type else "") +\
                    (" = " + default_code if field.default_ else "")
                fields.append(var_code)
        if fields:
            fields.append("")
        field_to_name = utils.invert_dict(type.__fields__)
        for name, field in fields_iter:
            if field.__type__ is context.objects.Func:
                func_code = context.unwrap(context.call_method(field, "source_bound", type, field_to_name[field]))
                fields.append(func_code)
        block_code = "\n".join(fields)
        code = "class" + ("({})".format(context.unwrap(context.operators.qualname.native(type.__base__))) if type.__base__ else "") + ":" + wrap_block(block_code)
        return code
    @attach(Class, "repr", sign="(this:Class)->String")
    @wraps(result=True)
    def class_repr(this):
        return "<class {}>".format(context.unwrap(context.operators.qualname.native(this)))
    @attach(BoundMethod, "repr", sign="(this:Func)->String")
    @wraps(result=True)
    def boundmethod_repr(this):
        name = utils.invert_dict(this.obj.__type__.__fields__)[this.func_]
        return "{}.{}".format(context.unwrap(context.operators.repr.native(this.obj)), name)
    @attach(Attr, "repr", sign="(this:Attr)->String")
    @wraps(result=True)
    def attr_repr(this):
        buf = []
        if this.type:
            buf.append("type={}".format(context.unwrap(context.operators.qualname.native(this.type))))
        if this.default_ is not None:
            buf.append("default_=macro {}".format(repr(this.default_)))
        return "Attr({})".format(", ".join(buf))
