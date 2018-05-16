from twocode import utils
from twocode.utils.code import inline_exc, InlineException
import twocode.utils.string

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
                    frame.append(context.obj.Object(context.scope_types.ObjectScope, object=scope["this"]))
                scope = {key: context.obj.Var(value) for key, value in scope.items()}
                frame.append(context.obj.Object(context.scope_types.Scope, __this__=scope))
                frame.append(context.obj.Object(context.scope_types.Scope, __this__={}))
                # cheated, fast creation construction?
                # test if it would be even possible with construct
                with context.FrameContext(frame):
                    context.eval(func.code, type="pass")
        except context.exc.Return as exc:
            return_value = exc.value
        if return_value is None:
            return_value = context.wrap(None)
        return return_value
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
    def pack_args(func, scope):
        """
            turns scope into (args, kwargs)

            used to call native functions
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
    def construct_call(type, args):
        Arg = context.obj.Arg
        # print("constr", type, args)
        func = context.obj.Func(native=lambda *args, **kwargs: context.construct(type, (list(args), kwargs)), args=[Arg("args", pack="args"), Arg("kwargs", pack="kwargs")])
        # weird
        return func, args
    def bound_method_call(bound_method, args):
        args, kwargs = args
        obj, func = bound_method.obj, bound_method.func_
        return func, ([obj, *args], kwargs)
    def obj_call(obj, args):
        args, kwargs = args
        func = context.impl(obj.__type__, "__call__")
        if not func:
            raise TypeError("{} object is not callable".format(context.unwrap(context.operators.qualname.native(obj.__type__))))
        return func, ([obj, *args], kwargs)
    def new(type):
        new = context.impl(type, "__new__")
        # new SHOULD set vars to null, its weird without it - fill the slots even WITHOUT their default values?
        # nah, do defaults
        if new:
            return context.call(new, ([], {}))
        return context.obj.Object(type)
    def inherit_chain(type):
        types = []
        while type:
            types.insert(0, type)
            type = type.__base__
        return types
    def inherit_fields(type):
        fields = {}
        for t in context.inherit_chain(type):
            for var, attr in t.__fields__.items():
                # if context.inherits(t, attr):
                # waiting to solve math.add(a, b)
                fields[var] = attr
        return fields
    def inherits(type, attr):
        if attr.__type__ is context.objects.Attr:
            return True
        try:
            func, args = context.callable(attr, ([], {}), inline_exc=True)
        except InlineException:
            raise Exception("field not var or callable: {}".format(twocode.utils.string.escape(attr)))
        if context.bound(func, type):
            return True
        return False
    def bound(func, type):
        return func.args and func.args[0].name == "this" # and func.args[0].type in context.inherit_chain(type)
        # waiting for types
    def construct(type, args):
        args, kwargs = args
        obj = context.new(type)
        frame = type.__frame__ if type.__frame__ is not None else [context.scope.get_env()]
        with context.FrameContext(frame):
            for var, attr in context.inherit_fields(type).items():
                if attr.__type__ is context.objects.Attr: #
                    if attr.default_:
                        setattr(obj, var, context.eval(attr.default_, type="expr"))
                    else:
                        # turn off, types dont work yet
                        impl = None
                        # impl = context.impl(attr.type.__type__, "__default__")
                        if impl:
                            setattr(obj, var, context.call(impl, ([], {})))
                        else:
                            setattr(obj, var, context.wrap(None))
        constructor = context.impl(type, "__init__")
        if constructor:
            context.call(constructor, ([obj, *args], kwargs))
        return obj
    def impl(type, name, signature=None):
        """
            the way to check if a type implements a method

            when a native type wants to access its method without the option of it being overridden,
            use type.__fields__[name] or type.__base__.__fields__[name] instead

            GETATTR PROBLEM:
            the context used to ask for implementation through getattr
            classess offer their functions through __getattr__, but inherit their own methods as well
            a class which defined a repr stopped printing
            __getattr__ makes sense for scope access, we can still edit code for interfaces






            MATH PROBLEM:


            accessing add(a, b) is weird
            you cannot do impl because the first argument isn't "this"
            you cannot even delegate from that to the type because it isn't an inherited field for the same reason
            and getattr-ing it from the class risks accessing some property of the class instead

            still mention, though, that all the class history have their own fields


            # should __getattr__ be inherited?
        """
        fields = context.inherit_fields(type)
        if not name in fields:
            return None
        func = fields[name]
        try:
            context.callable(func, ([], {}), inline_exc=True)
        except InlineException:
            return None
        return func
        # signature
        # interface? for vars?

        # in python, which uses __new__ and alike the most, ALL funcs are inherited. you do def x() with no self and C(B) has it
        # you cascade until you find a __new__, same for add, which is static. everything is really
        # but obj.f must have f have this

    for name, instruction in utils.redict(locals(), "context".split()).items():
        setattr(context, name, instruction)
