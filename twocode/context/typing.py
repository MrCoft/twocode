from twocode.utils.code import InlineException, type_check_decor
from twocode import utils

def add_typing(context):
    Class, Func = [context.obj[name] for name in "Class, Func".split(", ")]
    wraps = context.native_wraps

    context.type_objects = utils.Object()
    def gen_class(name):
        cls = Class()
        context.type_objects[name] = cls
        return cls
    def attach(cls, name, **kwargs):
        def wrap(func):
            cls.__fields__[name] = Func(native=func, **kwargs)
        return wrap

    Type = gen_class("Type")
    ClassType = gen_class("ClassType")
    ClassType.__base__ = Type
    ParamType = gen_class("ParamType")
    ParamType.__base__ = ClassType
    FuncType = gen_class("FuncType")
    FuncType.__base__ = Type

    # in class
    # visible as List.T
    # in obj
    # T means the type param

    # getattr
    # internals

    # type param in func args "evals" to a specific type in an object
        # boundmethods have a specific type!
        # to __type_params__[type_param]

    # what node evals to change
    # class<T>: - expr_class
        # add params, eval methods correctly
    # List<T>() - term_call
    # constructor - __type_params__
    # T is visible correctly from within
    def type_obj(type):
        '''Turns a Class object into a ClassType.'''
        # lets absolutely do a obj->string function, for errors everywhere
        # any param can itself be a type object. or maybe it has to be. yes, it has to be.
        # wtf is "type_obj" then

        # still fail though, you need the instance itself!
        if isinstance(type, context.obj.Ref):
            type = type.__refobj__
        # next time:
        # here we check whether it's a class object and turn it into a ClassType

        # ClassType, ParamType, FuncType
        context.obj.Object(FuncType, args=args, return_type=return_type)
        # if class, to ClassType
        # if not type, fail
        # not ref though
        return type
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
        type = context.type_obj(type)
        fields = context.inherit_fields(type)
        if not name in fields:
            return None
        func = fields[name] # weird. i mean, i guess its not getattr, but is it a ref to self? class.getatttr?
        func = context.obj.Ref(func, func.__type__)
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
    @type_check_decor(obj=context.obj.Ref)
    def convert(obj, type):
        type = context.type_obj(type)
        if type.__type__ is context.objects.Func:
            return obj
            # exact same signature
        if context.extends(obj.__type__, type):
            return obj

        if obj.__type__ is context.basic_types.Null: # unwrap
            impl = context.impl(obj.__type__, "__default__")
            if impl:
                return context.call(impl, ([], {}))

        convert = context.impl(obj.__type__, "__to__")
        if convert:
            try:
                return context.call(convert, ([obj, type], {}))
            except TypeError: pass
        convert = context.impl(type, "__from__")
        if convert:
            try:
                return context.call(convert, ([obj], {}))
            except TypeError: pass

        raise context.exc.ConversionError("can't convert {} to {}".format(repr(obj.__type__), repr(type)))

    for name in "type_obj impl convert".split():
        context.__dict__[name] = locals()[name]

    class ConversionError(Exception):
        pass
    context.exc.ConversionError = ConversionError

# constrains, itreenode
# optional args

def sign_typing(context):
    Type, ClassType, ParamType, FuncType = [context.type_objects[name] for name in "Type, ClassType, ParamType, FuncType".split(", ")]
    w, uw, r, dr = [context.type_magic[name] for name in "w, uw, r, dr".split(", ")]
    wraps = context.native_wraps
    ar = context.AttrRefs

    add_vars = context.setup.add_vars

    add_vars(ClassType, """
        var class_:Class
    """)
    add_vars(ParamType, """
        var params:List<Type> = []
    """)
    add_vars(FuncType, """
        var args:List<Type> = []
        var return_type:Type
    """)

    def attach(cls, name, **kwargs):
        def wrap(func):
            cls.__fields__[name] = context.obj.Func(native=func, **kwargs)
        return wrap

    # literals?
    # add_vars(TypeParam, """
    # """) # constraint:Type

    @attach(ClassType, "source", sign="(this:ClassType)->String")
    def classtype_source(this):
        return context.operators.qualname.native(ar(this).class_)
    @attach(ParamType, "source", sign="(this:ParamType)->String")
    @wraps(result=True)
    def paramtype_source(this):
        return uw@ context.call(context.impl(ParamType.__base__, "source"), ([this], {})) + "<{}>".format(",".join(
            uw@ context.call_method(param, "source") for param in context.AttrWrapper(this).params
        ))
    @attach(FuncType, "source", sign="(this:FuncType)->String")
    @wraps(result=True)
    def functype_source(this):
        w_this = context.AttrWrapper(this)
        args = [uw@ context.call_method(r@ arg, "source") for arg in w_this.args]
        return_type = uw@ context.call_method(w_this.return_type, "source") if w_this.return_type else "()"
        return "({})->{}".format(",".join(args), return_type)
    @attach(context.objects.Func, "__get_type__", sign="(f:Func)->Type")
    def get_type(f):
        args = []
        for arg in f.args:
            if arg.macro_:
                args.append(context.obj.Ref.Object(ClassType, class_=context.node_types.Code))
                continue
            arg_type = arg.type if arg.type else context.obj.Ref.Object(ClassType, class_=context.basic_types.Object)
            if arg.pack == "args":
                arg_type = context.obj.Ref.Object(ParamType, class_=context.basic_types.List, params=(w@ [arg_type]).__refobj__)
            if arg.pack == "kwargs":
                arg_type = context.obj.Ref.Object(ParamType, class_=context.basic_types.Map, params=(w@ [context.obj.Ref.Object(ClassType, class_=context.basic_types.String), arg_type]).__refobj__)
            args.append(arg_type)
        args = (w@ args).__refobj__
        return_type = ar(f).return_type.__refobj__
        type = context.obj.Object(FuncType, args=args, return_type=return_type)
        return type

    # very often it's stored like just class
    # and we do type_obj
    # in internals

    # type_obj needs the instance though
    # so a List<float> can pull the float from type params
    # and this already uses the operator in func's case
