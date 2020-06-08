'''
from twocode import utils
from twocode.utils.code import inline_exc, InlineException
import twocode.utils.string
from twocode.utils.code import type_check_decor

def add_exceptions(context):
    class Return(Exception):
        def __init__(self, value=None):
            self.value = value
    class Break(Exception):
        pass
    class Continue(Exception):
        pass
    class EvalException(Exception):
        pass
    class RuntimeInterrupt(Exception):
        "stop the evaluation of current statement"

    class InvalidIfChainEmpty(Exception):
        "if_chain node has no if_blocks"
    class InvalidIfCondEmpty(Exception):
        "if_block node has empty condition"

    class InvalidPack(Exception):
        "arguments pack in wrong order"
    class InvalidUnpack(Exception):
        "arguments unpack in wrong order"

    context.exc = utils.Object()
    for name, exception in utils.redict(locals(), "context".split()).items():
        context.exc[name] = exception

def add_core(context):
    @type_check_decor(func=context.obj.Ref, result=context.obj.Ref)
    def call(func, args):
        """
            func can be any callable
            args don't have to be wrapped
            macro has been applied

            used by many context parts
            not used by term_call because of macro arguments

            NOTE:
            we use (args, kwargs) because *args, **kwargs aren't universal
            an (obj, *args, **kwargs) signature can't pass an "obj" keyword
        """
        func, (args, kwargs) = context.callable(func, args)
        scope = context.unpack_args(func, (args, kwargs))
        # error
        # if not in scope, but in args, and not pack

        # nam value   key arg
        return context.call_func(func, scope)
    def call_method(obj, method, *args):
        """
            an utility function
            it lacks **kwargs for safety
        """
        return context.call(context.impl(obj.__type__, method), ([obj, *args], {}))
    @type_check_decor(func=context.obj.Ref, result=context.obj.Ref)
    def call_func(func, scope):
        """
            expects a scope
            args, kwargs packed
            wraps args and sets defaults as neither call nor term_call need to do it
        """
        scope = {name: context.wrap(arg) for name, arg in scope.items()} # down
        # wrong args error where? test for exact msg
        # ex f(a, b) f(1) - missing positional argument -   f(a, pos=b) when there's no pos
        # missing keyword argument when there's no default
        for arg in func.args:
            if arg.default_:
                if arg.name not in scope:
                    scope[arg.name] = context.eval(arg.default_, type="expr")
        try:
            return_value = None
            if func.native:
                # NOTE:
                # does not swap the frame for efficiency
                # this does not limit functionality
                args, kwargs = context.pack_args(func, scope)
                return_value = func.native(*args, **kwargs)
            else:
                frame = func.frame.copy() if func.frame is not None else [context.scope.get_env()]
                bound = "this" in scope and context.bound(func, scope["this"].__type__)
                # weird. if the type was a mismatch we would not be calling it.
                if bound:
                    frame.append(context.obj.Ref.Object(context.scope_types.ObjectScope, object=scope["this"]))
                scope = {key: context.obj.Object(context.scope_types.Var, value=value.__refobj__, type=value.__reftype__) for key, value in scope.items()}
                frame.append(context.obj.Ref.Object(context.scope_types.Scope, __this__=scope))
                frame.append(context.obj.Ref.Object(context.scope_types.Scope, __this__={}))
                # cheated, fast creation construction?
                # test if it would be even possible with construct
                with context.FrameContext(frame):
                    context.eval(func.code, type="pass")
        except context.exc.Return as exc:
            return_value = exc.value
        if return_value is None:
            return_value = context.wrap(None)
        return return_value
    @type_check_decor(func=context.obj.Ref)
    def unpack_args(func, args):
        """
            uses the func's args to parse (args, kwargs) into a scope

            is transparent to moved values
            because term_call needs named slots to macro

            used by call and term_call
        """ # named
        # test all of these errors
        args, kwargs = args
        missing_pos = []
        scope = {}
        for arg in func.args:
            if not arg.pack:
                if args:
                    scope[arg.name] = args.pop(0)
                elif arg.name in kwargs:
                    scope[arg.name] = kwargs.pop(arg.name)
                else:
                    missing_pos.append(arg.name)

                    #: takes exactly 3 arguments (1 given)

                    # f() missing 1 required keyword-only argument: 'w'
                    # after pos
            elif arg.pack == "args":
                scope[arg.name] = args
                args = []
            elif arg.pack == "kwargs":
                scope[arg.name] = kwargs
                kwargs = {}


        # python's error handling

        # in case of a major fuckup, do provide all
        # in case it's simple, do provide simple messages

        if kwargs:
            # python complains about the first(random) of the extra keywords)
            raise TypeError("func{} missing {} required positional argument{}: {}".format(
                context.unwrap(context.call_method(func, "signature")),
                len(missing_pos),
                "s" if len(missing_pos) >= 2 else "",
                name_enum
            ))

        # f() got an unexpected keyword argument 'h'
        # f() got unexpected keyword arguments 'h', "a", "b"
        # only one of them
        if False and missing_pos:
            # optional though?
            missing_pos = [utils.string.escape(name) for name in missing_pos]
            if len(missing_pos) == 1:
                name_enum = missing_pos[0]
            elif len(missing_pos) == 2:
                name_enum = "{} and {}".format(missing_pos)
            else:
                name_enum = ", ".join(missing_pos[:-1]) + ", and " + missing_pos[-1]
            raise TypeError("func{} missing {} required positional argument{}: {}".format(
                context.unwrap(context.call_method(func, "signature")),
                len(missing_pos),
                "s" if len(missing_pos) >= 2 else "",
                name_enum
            ))
        # f() missing 1 required keyword-only argument: 'w'


        #if args or kwargs or missing_pos:




        if args or kwargs:
            # TypeError: f() got an unexpected keyword argument 'x'
            # f() takes 3 positional arguments but 6 were given

            # if both, complain about kwargs first

            raise SyntaxError("signature mismatch while unpacking arguments")

            # saying what sign it has helps
            # >>> f(**dict(a=2, b=3))
            # Traceback (most recent call last):
            #   File "<stdin>", line 1, in <module>
            # TypeError: f() got an unexpected keyword argument 'b'

            # unused arguments
            raise SyntaxError("unused arguments: {}".format(" ".join(kwargs.keys())))
        return scope
    @type_check_decor(func=context.obj.Ref)
    def pack_args(func, scope):
        """
            turns scope into (args, kwargs)
            used to call native functions

            NOTE: *args contain Ref.Objects as an unwrapped List would
            think of it as Twocode packing, not Python packing
        """
        args, kwargs = [], {}
        level = 0
        for arg in func.args:
            if not arg.pack: # ERRORS ON NAMES?
                if level == 0:
                    args.append(scope[arg.name])
                else:
                    kwargs[arg.name] = scope[arg.name]
            elif arg.pack == "args":
                args.extend(context.unwrap(scope[arg.name]))
                level = 1
            elif arg.pack == "kwargs":
                kwargs.update(context.unwrap(scope[arg.name]))
                level = 2
            del scope[arg.name]
        if scope:
            # print("ERR", scope.keys())
            raise SyntaxError("signature mismatch while packing arguments")

        return args, kwargs
    def pack_level(pack, name=None):
        if name: return 2
        if not pack: return 0
        if pack == "args": return 1
        if pack == "kwargs": return 2
    @inline_exc(TypeError)
    @type_check_decor(obj=context.obj.Ref)
    def callable(obj, args):
        while True:
            if obj.__type__ is context.objects.Func:
                return obj, args
            elif obj.__type__ is context.objects.Class:
                obj, args = construct_call(obj, args)
            elif obj.__type__ is context.objects.BoundMethod:
                obj, args = bound_method_call(obj, args)
            elif context.impl(obj.__type__, "__call__"):
                obj, args = obj_call(obj, args)
            else:
                raise InlineException("{} object is not callable".format(context.unwrap(context.operators.qualname.native(obj.__type__))))
    @type_check_decor(type=context.obj.Ref)
    def construct_call(type, args):
        Arg = context.obj.Arg
        func = context.obj.Func(native=lambda *args, **kwargs:
            context.construct(type, ([context.obj.Ref(value, context.basic_types.Object) for value in args], {name: context.obj.Ref(value, context.basic_types.Object) for name, value in kwargs.items()})),
        args=[Arg("args", pack="args"), Arg("kwargs", pack="kwargs")])
        func = context.obj.Ref(func, context.objects.Func)
        # weird
        return func, args
    def bound_method_call(bound_method, args):
        args, kwargs = args
        obj, func = bound_method.obj, bound_method.func_
        obj, func = context.obj.Ref(obj, context.basic_types.Object), context.obj.Ref(func, context.objects.Func) #
        return func, ([obj, *args], kwargs)
    @type_check_decor(obj=context.obj.Ref)
    def obj_call(obj, args):
        args, kwargs = args
        func = context.impl(obj.__type__, "__call__")
        if not func:
            raise TypeError("{} object is not callable".format(context.unwrap(context.operators.qualname.native(obj.__type__))))
        return func, ([obj, *args], kwargs)
    def new(type):
        type = context.type_obj(type)
        new = context.impl(type, "__new__")
        # new SHOULD set vars to null, its weird without it - fill the slots even WITHOUT their default values?
        # nah, do defaults
        if new:
            return context.call(new, ([], {}))
        return context.obj.Object(type)
    def inherit_chain(type):
        type = context.type_obj(type)
        types = []
        while type:
            types.insert(0, type)
            type = type.__base__
        return types
    @type_check_decor(base=context.obj.Ref.Object)
    def extends(type, base):
        type = context.type_obj(type)
        return base in context.inherit_chain(type)
    def inherit_fields(type):
        type = context.type_obj(type)
        fields = {}
        for t in context.inherit_chain(type):
            for var, attr in t.__fields__.items():
                # if context.inherits(t, attr):
                # waiting to solve math.add(a, b)
                fields[var] = attr
        return fields
    @type_check_decor(attr=context.obj.Ref)
    def inherits(type, attr):
        type = context.type_obj(type)
        if attr.__type__ is context.objects.Attr: #
            return True
        try:
            func, args = context.callable(attr, ([], {}), inline_exc=True)
        except InlineException:
            raise Exception("field not var or callable: {}".format(twocode.utils.string.escape(attr)))
        if context.bound(func, type):
            return True
        return False
    @type_check_decor(func=context.obj.Ref)
    def bound(func, type):
        type = context.type_obj(type)
        return func.args and func.args[0].name == "this" # and func.args[0].type in context.inherit_chain(type)
        # waiting for types
    def construct(type, args):
        type = context.type_obj(type)
        args, kwargs = args
        obj = context.new(type)
        frame = type.__frame__ if type.__frame__ is not None else [context.scope.get_env()]
        with context.FrameContext(frame):
            for var, attr in context.inherit_fields(type).items():
                if attr.__type__ is context.objects.Attr: #
                    if attr.default_:
                        setattr(obj, var, context.eval(attr.default_, type="expr").__refobj__)
                    else:
                        # turn off, types dont work yet
                        impl = None
                        # impl = context.impl(attr.type.__type__, "__default__")
                        if impl:
                            setattr(obj, var, context.call(impl, ([], {})).__refobj__)
                        else:
                            setattr(obj, var, context.wrap(None).__refobj__)
        constructor = context.impl(type, "__init__")
        if constructor:
            context.call(constructor, ([obj, *args], kwargs))
        return obj

    for name, instruction in utils.redict(locals(), "context".split()).items():
        setattr(context, name, instruction)

'''