from twocode.context.new.setup import type_check_decor


@type_check_decor()  # func=context.obj.Ref, result=context.obj.Ref)
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
    return _c.call_func(func, scope)

