from twocode import Utils
import textwrap

def add_setup(context):
    """
        a solution to the problem of building the context

        gives the context some temporary functionality
        that removes sign-related dependency between its parts

        DO NOT USE THE CONTEXT WHILE BUILDING IT:
        we can't call interpreted functions, context eval or declare
        constructs work because native does not swap the frame

        SIGN:
        a proper sign() would be useful from the very start
        possible solutions:
        - an alternate eval that stores types to resolve them later
            break eval into instructions, temporarily replace term_id
        - temporary context.scope
            the same as an alternate eval, really
            it would use a special name resolution
        we choose the temp scope

        DELAYED TYPING:
        scope looks for names in context.get_builtins()
        and returns None instead of failing
        sign and add_vars work immediatelly, skipping some types
        flush runs incomplete typing again
    """

    setup = Utils.Object()
    context.setup = setup

    setup.lookup_success = None
    setup.failed_signs = []
    setup.failed_vars = []

    class TempScope:
        def __getitem__(self, name):
            builtins = context.get_builtins()
            if name in builtins:
                return builtins[name]
            setup.lookup_success = False
            return None
        def __setitem__(self, name, value):
            raise NameError("can't set in temporary scope")
        def frame_copy(self):
            return None
        def get_env(self):
            # REASON: object repr in setup.end error message
            return context.obj.Object(context.scope_types.Env, __qualnames__=context.wrap(Utils.invert_dict(context.get_builtins())))
    context.scope = TempScope()

    def sign(func, signature):
        setup.lookup_success = True

        code = "func{}: {{}}".format(signature)
        try:
            func_obj = context.eval(context.parse(code))
        except NameError:
            # NOTE: sign funcs work in both scopes the same way to collect all errors
            setup.lookup_success = False
        else:
            func.args = func_obj.args
            func.return_type = func_obj.return_type

        if not setup.lookup_success:
            setup.failed_signs.append((func, signature))
    setup.sign = sign

    def add_vars(type, vars):
        setup.lookup_success = True
        vars = textwrap.dedent(vars).strip()

        code = "class:\n{}".format(textwrap.indent(vars, " " * 4))
        try:
            type_obj = context.eval(context.parse(code))
        except NameError:
            setup.lookup_success = False
        else:
            type.__fields__.update(type_obj.__fields__)

        if not setup.lookup_success:
            setup.failed_vars.append((type, vars))
    setup.add_vars = add_vars

    def flush_typing():
        signs, vars = setup.failed_signs, setup.failed_vars
        setup.failed_signs, setup.failed_vars = [], []
        for args in signs:
            setup.sign(*args)
        for args in vars:
            setup.add_vars(*args)
    setup.flush_typing = flush_typing

    def end():
        setup.flush_typing()
        if setup.failed_signs or setup.failed_vars:
            raise Exception("can't complete setup typing:\n{}".format("\n".join(repr(args) for failed in [setup.failed_signs, setup.failed_vars] for args in failed)))
        del context.setup
    setup.end = end