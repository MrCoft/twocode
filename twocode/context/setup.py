from twocode import utils
from twocode.utils.code import type_check
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

    setup = utils.Object()
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
            return context.obj.Object(context.scope_types.Env, __qualnames__=context.wrap(utils.invert_dict(context.get_builtins())))
    context.scope = TempScope()

    def sign(func, signature):
        setup.lookup_success = True

        code = "func{}: {{}}".format(signature)
        try:
            func_obj = context.eval(context.parse(code), type="expr")
        except NameError:
            # NOTE: sign funcs work in both scopes the same way to collect all errors
            setup.lookup_success = False
        else:
            func.args = func_obj.args
            func.return_type = func_obj.return_type

        if not setup.lookup_success:
            setup.failed_signs.append((func, signature))
    setup.sign = sign

    def add_vars(cls, vars):
        setup.lookup_success = True
        vars = textwrap.dedent(vars).strip()

        code = "class:\n{}".format(textwrap.indent(vars, " " * 4))
        try:
            type_obj = context.eval(context.parse(code), type="expr")
        except NameError:
            setup.lookup_success = False
        else:
            cls.__fields__.update(type_obj.__fields__)

        if not setup.lookup_success:
            setup.failed_vars.append((cls, vars))
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
            raise Exception("can't complete setup typing:\n{}".format("\n".join(str(args) for failed in [setup.failed_signs, setup.failed_vars] for args in failed)))
        del context.setup
    setup.end = end

    # SETUP: utils
    class AttrRefs:
        def __init__(self, obj):
            type_check(obj, context.obj.Ref)
            self.__dict__["__this__"] = obj
        def __getattr__(self, name):
            return context.getattr(self.__this__, name)
        def __setattr__(self, name, value):
            context.setattr(self.__this__, name, value)
    context.AttrRefs = AttrRefs
    class AttrWrapper:
        def __init__(self, obj):
            type_check(obj, context.obj.Ref)
            self.__dict__["__this__"] = obj
        def __getattr__(self, name):
            return context.unwrap(context.getattr(self.__this__, name))
        def __setattr__(self, name, value):
            context.setattr(self.__this__, name, context.wrap(value))
    context.AttrWrapper = AttrWrapper

    type_magic = utils.Object()
    context.type_magic = type_magic
    class MatmulMagic:
        def __init__(self, map, call=None):
            self.map = map
            self.call = call
        def __matmul__(self, obj):
            if isinstance(obj, MatmulMagic):
                return MatmulMagic(lambda obj2: self.map(obj@ obj2))
            return self.map(obj)
        def __call__(self, *args, **kwargs):
            if self.call:
                return self.call(*args, **kwargs)
            else:
                return self.map(*args, **kwargs)
    type_magic.MatmulMagic = MatmulMagic
    type_magic.w = MatmulMagic(lambda obj: context.wrap(obj))
    type_magic.uw = MatmulMagic(lambda obj: context.unwrap(obj))
    type_magic.r = MatmulMagic(lambda obj: context.obj.Ref(obj, context.basic_types.Object), lambda type: MatmulMagic(lambda obj: context.obj.Ref(obj, type)))
    type_magic.dr = MatmulMagic(lambda obj: context.obj.Ref.deref(obj))
    class Operators:
        def __getattr__(self, name):
            op = context.operators[name]
            return lambda *args, **kwargs: context.unwrap(op.native(*args, **kwargs))
    type_magic.op = Operators()
