import types
from .ref import Ref
from .object import Object as _Object
# import twocode.context.new.objects.attr as attr
from .attr import *
from . import create


# noinspection PyPep8Naming
def Object(__type__, **kwargs):
    return Ref(_Object(__type__, **kwargs), __type__)


global_mod = types.SimpleNamespace()  # attr)

'''
from twocode import utils
from twocode.lang.source import wrap_block, pack_args
from twocode.utils.code import inline_exc, InlineException, map_args, type_check_decor, type_check
import functools
import builtins


# automatic python object

# fail qualname?
# an ensure is not null or error func?
    #  at func_repr
# is this how i call funcs?
    # repr_bound in class_repr

def add_objects(context):
    def wraps(*names, result=False):
        map = {name: lambda obj: context.unwrap(obj) for name in names}
        # NOTE: unwrap can't be passed yet, it would be weird to isolate its definition out
        wrap_args = map_args(map)
        def wrap(f):
            f = wrap_args(f)
            @functools.wraps(f)
            def wrapped(*args, **kwargs):
                return_value = f(*args, **kwargs)
                if result:
                    return_value = context.wrap(return_value)
                return return_value
            return wrapped
        return wrap
    context.native_wraps = wraps

    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .objects import ContextObj
    context.obj: ContextObj = utils.Object()

    w, uw, r, dr, op = [context.type_magic[name] for name in "w, uw, r, dr, op".split(", ")]




    for name in "hasattr getattr setattr".split():
        context.__dict__[name] = locals()[name]




    

    

    context.objects = utils.Object()
    context.objects.Class = None
    Class = context.obj.Class()
    Class.__type__ = Class
    context.objects.Class = Class
    def gen_class(name):
        cls = context.obj.Class()
        context.objects[name] = cls
        return cls
    Func = gen_class("Func")
    Arg = gen_class("Arg")
    Attr = gen_class("Attr")
    BoundMethod = gen_class("BoundMethod")

def sign_objects(context):
    Func, Arg, Class, Attr, BoundMethod = [context.objects[name] for name in "Func, Arg, Class, Attr, BoundMethod".split(", ")]
    w, uw, r, dr, op = [context.type_magic[name] for name in "w, uw, r, dr, op".split(", ")]

    add_vars = context.setup.add_vars

    # internals are set to wrapped null when constructed
    # class fields to {}
    add_vars(Func, """
        var args:List<Arg> = []
        var return_type:Class
        var code:Code
        var native:Func
        var frame:List<Scope>
    """)
    add_vars(Arg, """
        var name:String
        var type:Class
        var default_:Code
        var pack:String
        var macro_:Bool = false
    """) # pack - native enum?
    add_vars(Class, """
        var __fields__:Map<String,Object> = []
        var __base__:Class
        var __params__:Map<String,Type> = []
        var __frame__:List<Scope>
    """)
    add_vars(Attr, """
        var type:Class
        var default_:Code
    """)
    add_vars(BoundMethod, """
        var obj:Object
        var func_:Func
    """)

    wraps = context.native_wraps
    ar = context.AttrRefs
    deref = context.obj.Ref.deref
    def attach(cls, name, **kwargs):
        def wrap(func):
            cls.__fields__[name] = context.obj.Func(native=func, **kwargs)
        return wrap

    @attach(Func, "__init__", sign="(this:Func, ?args:List<Arg>, ?return_type:Class, ?code:Code, ?sign:String)")
    @wraps("args", "return_type", "sign")
    def func_init(this, args=None, return_type=None, code=None, sign=None):
        if args is None: args = []
        this.args = args
        this.return_type = dr@ return_type
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
    @wraps("name", "type", "pack", "macro_")
    def arg_init(this, name, type=None, default_=None, pack="", macro_=False):
        this.name = name
        this.type = dr@ type
        this.default_ = context.unwrap_code(default_)
        this.pack = pack
        this.macro_ = macro_
    @attach(Class, "__init__", sign="(this:Class)")
    def class_init(this):
        this.__fields__ = {}
        this.__base__ = None
        this.__frame__ = None
    @attach(Attr, "__init__", sign="(this:Attr, ?type:Class, ?default_:Code)")
    @wraps("type")
    def attr_init(this, type=None, default_=None):
        this.type = dr@ type
        this.default_ = context.unwrap_code(default_)
    @attach(BoundMethod, "__init__", sign="(this:BoundMethod, obj:Object, func_:Func)")
    def boundmethod_init(this, obj, func_):
        this.obj = dr@ obj
        this.func_ = dr@ func_

    @attach(Class, "__getattr__", sign="(this:Class, name:String)->Object")
    @wraps("name")
    @inline_exc(AttributeError)
    def class_getattr(this, name):
        fields = this.__fields__
        if name in fields:
            attr = r(context.objects.Attr)@ fields[name]
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
            # is this meant to rewrite fields? or is it static var writing
            this.__fields__[name] = value.__refobj__
            return
        raise InlineException()
    @attach(Func, "signature", sign="(f:Func, ?cls:Class)->String")
    @wraps("cls", result=True)
    def func_signature(f, cls=None):
        bound = cls and context.bound(f, cls)
        args = []
        for arg in f.args if not bound else f.args[1:]:
            if not arg.name:
                raise ValueError("unnamed argument")
            arg_code =\
                pack_args(arg.pack) +\
                ("macro " if arg.macro_ else "") +\
                arg.name +\
                (":{}".format(op.qualname(ar(arg).type)) if arg.type else "") +\
                ("={}".format(str(arg.default_)) if arg.default_ else "")
            args.append(arg_code)
        code =\
            "({})".format(", ".join(args)) +\
            ("->{}".format(op.qualname(ar(f).return_type)) if f.return_type else "")
        return code
    @attach(Func, "source_bound", sign="(f:Func, ?cls:Class, ?name:String)->String")
    @wraps("cls", "name", result=True)
    def func_source_bound(f, cls=None, name=None):
        static = cls and not context.bound(f, cls)
        signature = uw@ context.call_method(f, "signature", cls)
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
    @attach(Func, "type", sign="(f:Func, ?cls:Class)->String")
    @wraps("cls", result=True)
    def func_type(f, cls=None):
        return uw@ context.call_method(context.call_method(f, "__get_type__"), "source")

        bound = cls and context.bound(f, cls)
        args = []
        for arg in f.args if not bound else f.args[1:]:
            arg_code =\
                pack_args(arg.pack) +\
                ("?" if arg.default_ else "") +\
                (op.qualname(ar(arg).type) if arg.type else "()")
            args.append(arg_code)
        code =\
            (("({})").format(",".join(args)) if len(args) != 1 else args[0]) +\
            "->" +\
            (op.qualname(ar(f).return_type) if f.return_type else "()")
        return code
    @attach(Func, "__repr__", sign="(f:Func)->String")
    @wraps(result=True)
    def func_repr(f):
        return "<func {}>".format(uw@ context.call_method(f, "type"))
    @attach(Arg, "__repr__", sign="(this:Arg)->String")
    @wraps(result=True)
    def arg_repr(this):
        buf = []
        buf.append(op.repr(w@ this.name))
        if this.type:
            buf.append(op.qualname(ar(this).type))
        if this.default_ is not None:
            buf.append("default_={}".format(repr(this.default_)))
        if this.pack:
            buf.append("pack={}".format(op.repr(w@ this.type)))
        if this.macro_:
            buf.append("macro_={}".format(op.repr(w@ this.macro_)))
        return "Arg({})".format(", ".join(buf))
    @attach(Class, "source", sign="(cls:Class)->String")
    @wraps(result=True)
    def class_source(cls):
        # @internal - for certain vars
        fields = []
        fields_iter = sorted((uw@ name, r(context.objects.Ref)@ field) for name, field in cls.__fields__.items())
        for name, field in fields_iter:
            if field.__type__ is context.objects.Attr:
                default_code = repr(field.default_)
                var_code =\
                    "var {}".format(name) +\
                    (":{}".format(op.qualnamee(ar(field).type)) if field.type else "") +\
                    (" = " + default_code if field.default_ else "")
                fields.append(var_code)
        if fields:
            fields.append("")
        field_to_name = utils.invert_dict(cls.__fields__)
        for name, field in fields_iter:
            if field.__type__ is context.objects.Func:
                func_code = uw@ context.call_method(field, "source_bound", cls, field_to_name[field])
                fields.append(func_code)
        block_code = "\n".join(fields)
        code = "class" + ("({})".format(op.qualname(ar(cls).__base__)) if cls.__base__ else "") + ":" + wrap_block(block_code)
        return code
    @attach(Class, "__repr__", sign="(this:Class)->String")
    @wraps(result=True)
    def class_repr(this):
        return "<class {}>".format(op.qualname(this))
    @attach(BoundMethod, "__repr__", sign="(this:Func)->String")
    @wraps(result=True)
    def boundmethod_repr(this):
        name = utils.invert_dict(this.obj.__type__.__fields__)[this.func_]
        return "{}.{}".format(op.repr(ar(this).obj), name)
    @attach(Attr, "__repr__", sign="(this:Attr)->String")
    @wraps(result=True)
    def attr_repr(this):
        buf = []
        if this.type:
            buf.append("type={}".format(op.qualname(ar(this).type)))
        if this.default_ is not None:
            buf.append("default_=macro {}".format(repr(this.default_)))
        return "Attr({})".format(", ".join(buf))

'''
