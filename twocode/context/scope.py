from twocode import utils
from twocode.utils.code import inline_exc, InlineException, type_check_decor, type_check
import os
from twocode.utils.string import escape

# TO FINISH:
# random #s




# parse func
# zip, native python

# import Entry
# this

# possibly, one day, implement program pointer stride and exceptions manually?
# how would that even work? i'd have to have always a complete stack of nodes i am currently in
# and be able to continue from any point i currently wrap in try except
# so unlike python code and a recursive eval

import twocode
codebase = os.path.join(os.path.dirname(os.path.dirname(twocode.__file__)), "code")
if not os.path.exists(os.path.join(codebase, "__package__.2c")):
    codebase = os.path.join(os.path.dirname(twocode.__file__), "code")
    if not os.path.exists(os.path.join(codebase, "__package__.2c")):
        raise Exception("Twocode codebase not found")

def add_scope(context):
    Object, Ref, Class, Func = [context.obj[name] for name in "Object, Ref, Class, Func".split(", ")]
    String, Map, NativeIterator = [context.basic_types[name] for name in "String, Map, NativeIterator".split(", ")]
    w, uw, r, dr, op = [context.type_magic[name] for name in "w, uw, r, dr, op".split(", ")]
    wraps = context.native_wraps

    @inline_exc(TypeError)
    @type_check_decor(value=context.obj.Ref)
    def declare(name, value, type):
        type = context.type_obj(type)
        scope = Ref(context.frame[-1], context.scope_types.Scope)
        impl = context.impl(scope.__type__, "declare")
        if impl:
            context.call(impl, ([scope, name, value, r@ type], {})) # , inline_exc=True ??   to Type
        else:
            raise InlineException("cannot declare in {}".format(op.qualname(scope.__type__)))
    def lookup(path):
        """
            DESIGN:
            called 3 times in module_getattr
            case sensitive, the only way to check that is to os.listdir at each step
            to call that for multiple similiar paths seems redundant,
            but each can be found in a different source
        """
        env = r(context.scope_types.Env)@ context.scope.get_env()
        sources = context.AttrWrapper(env).__sources__ # can't get to it in context, unwrapped
        for source in sources:
            source = uw@ r@ source
            if isinstance(source, str):
                file = utils.case_path(path, dir=source)
                if file:
                    return file
            else:
                # interface
                pass
    @inline_exc(ImportError)
    def imp(path):
        path = path.split(".")
        try:
            module = r(context.scope_types.Env)@ context.scope.get_env()
            for i, name in enumerate(path):
                module = context.call_method(module, "imp", name)
            return module
        except ImportError:
            raise InlineException("no module named {}".format(escape(".".join(path[:i + 1])))) from None
    for name in "declare lookup imp".split():
        context.__dict__[name] = locals()[name]

    context.scope_types = utils.Object()
    def gen_class(name):
        cls = Class()
        context.scope_types[name] = cls
        return cls
    def attach(cls, name, **kwargs):
        def wrap(func):
            cls.__fields__[name] = Func(native=func, **kwargs)
        return wrap

    """
        DESIGN:
        Scope
            a variable layer unit, a map of typed slots
        stack frame
            a stack of scope layers
            each layer sees variables at and below itself
            defined mostly by a module path, has an Env at the bottom
        call stack
            the call history, swapped out frames
            each stack frame may be in a different module
            has the entry's main and top-level code at the bottom
    """
    Var = gen_class("Var")
    Scope = gen_class("Scope")
    ObjectScope = gen_class("ObjectScope")
    Module = gen_class("Module")
    Module.__base__ = Scope
    Env = gen_class("Env")
    Env.__base__ = Module
    Env.__frame__ = []
    # REASON:
    # context swaps to env when the class doesn't have a frame,
    # which we can't do while building the env

    add_vars = context.setup.add_vars

    add_vars(Var, """
        var value:Object
        var type:Class
    """)
    add_vars(ObjectScope, """
        var object:Object
    """)
    add_vars(Module, """
        var __path__:String
        var __file__:String
        var __defaults__
    """)
    add_vars(Env, """
        var __sources__:List<String> = []
        var __qualnames__:Map<Object,String> = []
    """)

    @attach(Var, "__init__", sign="(this:Var, ?value:Object, type:Class)")
    def var_init(this, value, type):
        w_this = context.AttrWrapper(this)
        w_this.value = value
        w_this.type = type
    @attach(Scope, "__init__", sign="(this:Scope, ?map:Map)")
    @wraps("map")
    def scope_init(this, map=None):
        # OPTIM: map not a var
        if map is None: map = {}
        this.__this__ = map
    @attach(Scope, "__getitem__", sign="(this:Scope, name:String)->Object")
    @wraps("name")
    @inline_exc(KeyError)
    def scope_getitem(this, name):
        var = this.__this__.get(name)
        if var:
            return Ref(var.value, var.type)
        raise InlineException()
    @attach(Scope, "__setitem__", sign="(this:Scope, name:String, value:Object)")
    @wraps("name")
    @inline_exc(KeyError)
    def scope_setitem(this, name, value):
        var = this.__this__.get(name)
        if var:
            var.value = context.convert(value, var.type).__refobj__
            return
        raise InlineException()
    @attach(Scope, "declare", sign="(this:Scope, name:String, value:Object, type:Class)")
    @wraps("name", "type")
    def scope_declare(this, name, value, type): # type=None?
        this.__this__[name] = context.obj.Object(Var, type=type)
        context.call_method(this, "__setitem__", name, value) # op?
    @attach(Scope, "__getattr__", sign="(this:Scope, name:String)->Object")
    @wraps("name")
    @inline_exc(AttributeError)
    def scope_getattr(this, name):
        try:
            return context.call_method(this, "__getitem__", name)
        except KeyError:
            pass
        raise InlineException()
    @attach(Scope, "__setattr__", sign="(this:Scope, name:String, value:Object)")
    @wraps("name")
    @inline_exc(AttributeError)
    def scope_setattr(this, name, value):
        try:
            context.call_method(this, "__setitem__", name, value)
        except KeyError:
            pass
        raise InlineException()
    @attach(Scope, "__contains__", sign="(this:Scope, item:String)->Bool")
    @wraps("item", result=True)
    def scope_contains(this, item):
        return item in this.__this__
    @attach(Scope, "keys", sign="(this:Scope)->List")
    def scope_keys(this):
        return Object(NativeIterator, __this__=map(context.wrap, this.__this__))
    @attach(Scope, "values", sign="(this:Scope)->List")
    def scope_values(this):
        return Object(NativeIterator, __this__=map(lambda var: r(var.type)@ var.value, this.__this__.values()))
    @attach(Scope, "items", sign="(this:Scope)->List")
    def scope_items(this):
        arg_map = lambda name, var: w@ (w@ name, r(var.type)@ var.value)
        return Object(NativeIterator, __this__=map(lambda args: arg_map(*args), this.__this__.items()))
    @attach(Scope, "vars", sign="(this:Scope)->Map")
    def scope_vars(this):
        # TODO: to field
        return w@ this.__this__
    @attach(Scope, "__iter__", sign="(this:Scope)->Iterable")
    def scope_iter(this):
        return context.call_method(this, "keys")
    @attach(ObjectScope, "__init__", sign="(this:ObjectScope, obj:Object)")
    def object_init(this, obj):
        w_this = context.AttrWrapper(this)
        w_this.object = obj
    @attach(ObjectScope, "__getitem__", sign="(this:ObjectScope, name:String)->Object")
    @wraps("name")
    @inline_exc(KeyError)
    def object_getitem(this, name):
        type = this.__type_params__.get(name) # layer by layer? sum of inheritance?
        if type:
            return r(context.type_objects.Type)@ type
        w_this = context.AttrWrapper(this)
        try:
            return context.getattr(w_this.object, name, inline_exc=True)
        except InlineException:
            pass
        raise InlineException()
    @attach(ObjectScope, "__setitem__", sign="(this:ObjectScope, name:String, value:Object)")
    @wraps("name")
    @inline_exc(KeyError)
    def object_setitem(this, name, value):
        type = this.__type_params__.get(name)
        if type:
            raise InlineException("cannot set type parameter")
        w_this = context.AttrWrapper(this)
        try:
            return context.setattr(w_this.object, name, value, inline_exc=True)
        except InlineException:
            pass
        raise InlineException()
    @attach(ObjectScope, "declare", sign="(this:ObjectScope, name:String, value:Object, type)")
    @wraps("name", "type")
    def object_declare(this, name, value, type):
        raise TypeError("cannot declare in object")
    @attach(Module, "__init__", sign="(this:Module, ?path:String, ?file:String)") #
    @wraps("path", "file")
    def module_init(this, path=None, file=None, uproot=False):
        context.call(context.impl(Module.__base__, "__init__"), ([this], {}))
        w_this = context.AttrWrapper(this)
        w_this.__path__ = path
        w_this.__file__ = os.path.abspath(file) if file else None
        w_this.__defaults__ = Object(context.scope_types.Scope, __this__={})
        # NOTE: has to be created directly while creating the Env
    @attach(Module, "__getitem__", sign="(this:Module, name:String)->Object")
    @wraps("name")
    @inline_exc(KeyError)
    def module_getitem(this, name):
        var = this.__this__.get(name)
        if var:
            return r(var.type)@ var.value
        try:
            return context.operators.getitem.native(this.__defaults__, name)
        except KeyError:
            pass
        w_this = context.AttrWrapper(this)
        if w_this.__path__ is not None:
            try:
                return context.call_method(this, "imp", name)
            except ImportError:
                pass
        raise InlineException()
    @attach(Module, "__setitem__", sign="(this:Module, name:String, value:Object)")
    @wraps("name")
    @inline_exc(KeyError)
    def module_setitem(this, name, value):
        var = this.__this__.get(name)
        if var:
            var.value = context.convert(value, var.type).__refobj__
            return
        if op.contains(this.__defaults__, w@ name):
            raise TypeError("cannot set defaults")
        raise InlineException()
    @attach(Module, "imp", sign="(this:Module, name:String)->Object")
    @wraps("name")
    @inline_exc(ImportError)
    def module_imp(this, name):
        var = this.__this__.get(name)
        if var:
            return Ref(var.value, var.type) # weird. otherwise imports delete a module, e.g. code which has all the goodies
        w_this = context.AttrWrapper(this)
        path = (w_this.__path__.split(".") if w_this.__path__ else []) + [name]
        filepath = os.path.join(*path)
        module = None
        module_file = context.lookup(filepath + ".2c")
        package_file = context.lookup(filepath)
        if module_file and package_file:
            raise InlineException("{} is both a module and a package".format(escape(".".join(path))))
        # __path__, or... __scope__ ?
        if module_file:
            module = context.construct(context.scope_types.Module, ([], {}))
            filename = module_file
        else:
            if package_file and os.path.isdir(package_file):
                module = context.construct(context.scope_types.Module, ([], {}))
                filename = context.lookup(filepath + os.path.sep + "__package__.2c")
        if module:
            """
                any full path is loaded module by module
                modules can be arbitrarily renamed, created
                and the file lookup happens from the path of this

                so "importing" is definitely a method of module

                importing:
                file vs dir
                exec ast in stack

                back: declare
            """
            module.__path__ = w@ ".".join(path)
            module.__defaults__.__this__.update(this.__defaults__.__this__)

            package = Ref(context.scope.get_env(), context.scope_types.Scope)
            with context.FrameContext([package.__refobj__]):
                if len(path) >= 2:
                    package = context.operators.getitem.native(package, path[0])
                    context.frame.append(package.__refobj__)
                    for package_name in path[1:-1]:
                        package = context.operators.getitem.native(package, package_name)
                        context.frame[-1] = package.__refobj__
                    context.declare(name, module, module.__reftype__)
                    context.frame[-1] = module.__refobj__
                else:
                    context.declare(name, module, module.__reftype__)
                    context.frame.append(module.__refobj__)

                if filename:
                    context.declare("__file__", w@ filename, String)
                    ast = context.parse(open(filename, encoding="utf-8").read())
                    #try:
                    context.eval(ast, type="stmt")

                    #except:
                        # delete
                        # any other exceptions raised are propagated up, aborting the import process
                        # cmnt somewhere?
                    #    raise
                return module
        else:
            raise InlineException("no module named {}".format(escape(".".join(path)))) from None
    @attach(Module, "declare", sign="(this:Module, name:String, value:Object, type:Class)")
    @wraps("name")
    def module_declare(this, name, value, type):
        w_this = context.AttrWrapper(this)
        if context.extends(value.__type__, context.objects.Class):
            qualname = op.qualname(value)
            if qualname is None:
                qualnames = context.scope.get_env().__qualnames__
                op.setitem(r@ qualnames, value, w@ ((w_this.__path__ + "." if w_this.__path__ else "") + name))
        context.call(context.impl(Module.__base__, "declare"), ([this, name, value, type], {}))
    @attach(Env, "__init__", sign="(this:Env)")
    def env_init(this):
        context.call(context.impl(Env.__base__, "__init__"), ([this, ""], {}))
        sources = []
        qualnames = {}
        for name, obj in (uw@ context.call_method(this, "builtins")).items():
            # NOTE:
            # builtins do not have special access, their qualnames become invalid if you override them
            # NOTE:
            # declare would use qualname, which would look up the frame[0] Env
            # the purpose of this is to register them here
            if context.extends(obj.__type__, context.objects.Class):
                qualnames[op.hash(r@ obj)] = (w@ name).__refobj__
            this.__this__[name] = context.obj.Object(Var, value=obj, type=obj.__type__) # refobj

        sources.append((w@ codebase).__refobj__)

        w_this = context.AttrWrapper(this)
        w_this.__sources__ = sources
        w_this.__qualnames__ = qualnames
    @attach(Env, "builtins", sign="(this:Env)->Map")
    @wraps(result=True)
    def env_builtins(this):
        return context.get_builtins()
    @attach(Env, "__code__")
    def env_code(this, code):
        pass

def scope_builtins(context):
    def get_builtins():
        builtins = {}
        for types_name in "objects basic_types scope_types exc_types builtins".split():
            types = getattr(context, types_name, None)
            # REASON:
            # while incomplete during setup, TempScope looks here
            # to resolve names such as objects and basic types
            if types:
                builtins.update(types)
        if hasattr(context, "operators"):
            for name in """
                repr qualname eval
                iter
                hasattr getattr setattr
            """.split():
                func = context.operators.get(name)
                if func:
                    builtins[name] = func
        if hasattr(context, "node_types"):
            builtins["Code"] = context.node_types.code
        return builtins
    context.get_builtins = get_builtins

"""
    DESIGN NOTE:

    We used to place types into the initial Env.

    This is wrong, because now class discovery in this Env
    finds e.g. all node types. It wouldn't find them
    in a new Env, where we can't access code.node_types at all
    because they don't exist.
    The only solution is to link these manually
    in the standard library.
"""

def init_scope(context):
    w, uw, r, dr = [context.type_magic[name] for name in "w, uw, r, dr".split(", ")]

    class FrameScope:
        def __init__(self):
            self.frame = []
        def __contains__(self, name):
            try:
                self[name]
            except NameError:
                return False
            else:
                return True
        @inline_exc(NameError) # KeyError?
        def __getitem__(self, name):
            for scope in reversed(self.frame):
                scope = r(context.scope_types.Scope)@ scope
                impl = context.impl(scope.__type__, "__getitem__")
                if not impl:
                    continue
                try:
                    return context.call(impl, ([scope, name], {})) # , inline_exc=True
                except KeyError:
                    pass
                if name == "this":
                    if scope.__type__ is context.scope_types.ObjectScope:
                        return scope.object
            raise InlineException("name {} is not defined".format(escape(name)))
        @inline_exc(NameError)
        def __setitem__(self, name, value):
            for scope in reversed(self.frame):
                scope = r(context.scope_types.Scope)@ scope
                impl = context.impl(scope.__type__, "__setitem__")
                if not impl:
                    continue
                try:
                    return context.call(impl, ([scope, name, value], {})) # , inline_exc=True
                except KeyError:
                    pass
                if name == "this":
                    if scope.__type__ is context.scope_types.ObjectScope:
                        raise InlineException("can't set {}".format(escape(name)))
            raise InlineException("name {} is not defined".format(escape(name)))
        def frame_copy(self):
            return self.frame.copy()
            # REASON: closure of signatures, abstracted for setup
        def get_env(self):
            env = self.frame[0]
            type_check(env, context.obj.Ref.Object)
            return env
            # REASON: frame[0] instead of stack[0][0] gets the CURRENT environment
    context.FrameScope = FrameScope
    class ScopeContext(utils.Context):
        def __enter__(self):
            context.frame.append(context.obj.Object(context.scope_types.Scope, __this__={}))
        def __exit__(self, exc_type, exc, tb):
            context.frame.pop()
    context.ScopeContext = ScopeContext
    class FrameContext(utils.Context):
        def __init__(self, frame):
            for scope in frame:
                type_check(scope, context.obj.Ref.Object)
            self.frame = frame
        def __enter__(self):
            context.stack.append(context.frame)
            context.frame = self.frame
            context.scope.frame = self.frame
        def __exit__(self, exc_type, exc, tb):
            frame = context.stack.pop()
            context.frame = frame
            context.scope.frame = frame
    context.FrameContext = FrameContext

    context.scope = FrameScope()
    context.frame = context.scope.frame
    context.stack = []

    env = context.construct(context.scope_types.Env, ([], {}))
    env.name = w@ "<env>"
    context.frame.append(env.__refobj__)

    # SCOPE: add std lib
    std_lib = utils.Object()
    context.std_lib = std_lib
    def imp_type(path):
        std_lib[path.split(".")[-1]] = context.imp(path)
    imp_type("code.iter.IntIterator")
    imp_type("code.native.NativeObject")
