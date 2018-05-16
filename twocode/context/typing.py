from twocode import utils

def add_typing(context):
    Class, Func = [context.obj[name] for name in "Class, Func".split(", ")]
    wraps = context.native_wraps

    def gen_type(name):
        type = Class()
        context.objects[name] = type
        return type
    def attach(type, name, **kwargs):
        def wrap(func):
            type.__fields__[name] = Func(native=func, **kwargs)
        return wrap

    Type = gen_type("Type")
    ClassType = gen_type("ClassType")
    ClassType.__base__ = Type
    FuncType = gen_type("FuncType")
    FuncType.__base__ = Type
    TypeParam = gen_type("TypeParam")

    add_vars = context.setup.add_vars

    add_vars(ClassType, """
        var class_:Class
        var params:List<TypeParam> = []
    """)
    add_vars(FuncType, """
        var args:List<Type> = []
        var return_type:Type
    """)
    # literals?
    add_vars(TypeParam, """
        var name:String
    """) # constraint:Type

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

    def convert(obj, type):
        if type.__type__ is context.objects.Func:
            return obj
            # exact same signature
        if type in context.inherit_chain(obj.__type__):
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

        raise context.exc.ConversionError()

    for name, instruction in utils.redict(locals(), "context".split()).items():
        context.__dict__[name] = instruction

    class ConversionError(Exception):
        pass
    context.exc.ConversionError = ConversionError

# constrains, itreenode
# optional args
# type obj of a function, of an object
# type params
