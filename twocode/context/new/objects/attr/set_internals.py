import twocode.context.new as _c


@inline_exc(AttributeError)
def set_internals(obj, name, value):
    if name == "__type__":
        raise InlineException("can't set attribute {} of {}".format(escape(name)))
    if name == "__reftype__":
        raise InlineException("can't set attribute {} of {}".format(escape(name)))
    if name == "__type_params__":
        raise InlineException("can't set attribute {} of {}".format(escape(name)))
    if obj.__type__ is context.objects.Func:
        if name == "args":
            obj.args = uw@ value
        if name == "return_type":
            obj.return_type = uw@ value
        if name == "code":
            obj.code = context.unwrap_code(value)
        if name == "native":
            raise InlineException("can't set attribute {} of {}".format(escape(name)))
        if name == "frame":
            obj.frame = uw@ value
    if obj.__type__ is context.objects.Arg:
        if name == "name":
            obj.name = uw@ value
        if name == "type":
            obj.type = uw@ value
        if name == "default_":
            obj.default_ = context.unwrap_code(value)
        if name == "pack":
            obj.pack = context.unwrap_code(value)
        if name == "macro_":
            obj.macro_ = uw@ value
    if obj.__type__ is context.objects.Class:
        if name == "__fields__":
            obj.__fields__ = uw@ value
        if name == "__base__":
            obj.__base__ = uw@ value
        if name == "__frame__":
            obj.__frame__ = uw@ value
    if obj.__type__ is context.objects.Attr:
        if name == "type":
            obj.type = uw@ value
        if name == "default_":
            obj.default_ = context.unwrap_code(value)
