import twocode.context.new as _c


# @inline_exc(AttributeError)
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
        return r(context.type_objects.Type)@ context.type_obj(obj.__type__)
    if name == "__reftype__":
        return r(context.type_objects.Type)@ context.type_obj(obj.__reftype__) # in multiple places though? if it's internal. return_type, arg.type?
    if name == "__type_params__":
        return w@ {name: r(context.Objects.Type)@ type for name, type in obj.__type_params__.items()} ###
    if obj.__type__ is context.objects.Func:
        if name == "args":
            return w@ obj.args
        if name == "return_type":
            return w@ obj.return_type
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
        if name == "native":
            return obj if obj.native else w@ None
        if name == "frame":
            return w@ obj.frame # should be stack frame, or... why not just a list of scopes?
    if obj.__type__ is context.objects.Arg:
        if name == "name":
            return w@ obj.name
        if name == "type":
            return w@ obj.type
        if name == "default_":
            return context.wrap_code(obj.default_)
        if name == "pack":
            return context.wrap_code(obj.pack)
        if name == "macro_":
            return w@ obj.macro_
    if obj.__type__ is context.objects.Class:
        if name == "__fields__":
            return w@ obj.__fields__
        if name == "__base__":
            return w@ obj.__base__
        if name == "__frame__":
            return w@ obj.__frame__
    if obj.__type__ is context.objects.Attr:
        if name == "type":
            return w@ obj.type
        if name == "default_":
            return context.wrap_code(obj.default_)
    raise InlineException()
