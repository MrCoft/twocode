

add_vars(Func, """
        var args:List<Arg> = []
        var return_type:Class
        var code:Code
        var native:Func
        var frame:List<Scope>
    """)


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
