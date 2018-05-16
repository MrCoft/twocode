from twocode import utils
from twocode.utils.code import inline_exc, InlineException
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
    @inline_exc(TypeError)
    def declare(name, value, type=None):
        scope = context.frame[-1]
        impl = context.impl(scope.__type__, "declare")
        if impl:
            context.call(impl, ([scope, name, value, type], {})) # , inline_exc=True ??
        else:
            raise InlineException("cannot declare in {}".format(context.unwrap(context.operators.qualname.native(scope.__type__))))
    def lookup(path):
        """
            DESIGN:
            called 3 times in module_getattr
            case sensitive, the only way to check that is to os.listdir at each step
            to call that for multiple similiar paths seems redundant,
            but each can be found in a different source
        """
        env = context.scope.get_env()
        sources = context.unwrap(env.__sources__) # can't get to it in context, unwrapped
        for source in sources:
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
            module = context.frame[0]
            for i, name in enumerate(path):
                module = context.call_method(module, "imp", name)
            return module
        except ImportError:
            raise InlineException("no module named {}".format(escape(".".join(path[:i + 1])))) from None
    for name, instruction in utils.redict(locals(), "context".split()).items():
        context.__dict__[name] = instruction

    Object, Class, Func, Var = [context.obj[name] for name in "Object, Class, Func, Var".split(", ")]
    String, Map, NativeIterator = [context.basic_types[name] for name in "String, Map, NativeIterator".split(", ")]
    wraps = context.native_wraps

    context.scope_types = utils.Object()
    def gen_type(name):
        type = Class()
        context.scope_types[name] = type
        return type
    def attach(type, name, **kwargs):
        def wrap(func):
            type.__fields__[name] = Func(native=func, **kwargs)
        return wrap

    """
        DESIGN:
        Scope
            a variable layer unit, a map of typed slots
        StackFrame
            a stack of scope layers
            each layer sees variables at and below itself
            defined mostly by a module path, has an Env at the bottom
        CallStack
            the call history, swapped out frames
            each stack frame may be in a different module
            has the entry's main and top-level code at the bottom
    """
    Scope = gen_type("Scope")
    ObjectScope = gen_type("ObjectScope")
    StackFrame = gen_type("StackFrame") # has list api
    CallStack = gen_type("CallStack")
    # from list
    Module = gen_type("Module")
    Module.__base__ = Scope
    Env = gen_type("Env")
    Env.__base__ = Module
    Env.__frame__ = []
    # REASON:
    # context swaps to env when the class doesn't have a frame,
    # which we can't do while building the env

    add_vars = context.setup.add_vars

    add_vars(ObjectScope, """
        var object:Object
    """)
    add_vars(Module, """
        var __path__:String
        var __file__:String
    """)
    add_vars(Env, """
        var __sources__:List<String> = []
        var __qualnames__:Map<Object,String> = []
    """)

    @attach(Scope, "__init__", sign="(this:Scope, ?map:Map)")
    @wraps("map")
    def scope_init(this, map=None):
        # NOTE: map not a var for speed
        if map is None: map = {}
        this.__this__ = map
    @attach(Scope, "__getattr__", sign="(this:Scope, name:String)->Object")
    @wraps("name")
    @inline_exc(AttributeError)
    def scope_getattr(this, name):
        if name in this.__this__:
            return this.__this__[name].value
        raise InlineException()
    @attach(Scope, "__setattr__", sign="(this:Scope, name:String, value:Object)")
    @wraps("name")
    @inline_exc(AttributeError)
    def scope_setattr(this, name, value):
        if name in this.__this__:
            this.__this__[name].value = value
            return
        raise InlineException()
    @attach(Scope, "declare", sign="(this:Scope, name:String, value:Object, ?type:Class)")
    @wraps("name", "type")
    def scope_declare(this, name, value, type=None):
        this.__this__[name] = Var(type=type)
        context.call_method(this, "__setattr__", name, value)
    @attach(Scope, "__getitem__", sign="(this:Scope, key:String)->Object")
    @wraps("name")
    def scope_getitem(this, key):
        return context.call_method(this, "__getattr__", key)
    @attach(Scope, "__setitem__", sign="(this:Scope, key:String, value:Object)")
    @wraps("name")
    def scope_setitem(this, key, value):
        context.call_method(this, "__setattr__", key, value)
    @attach(Scope, "contains", sign="(this:Scope, item:String)->Bool")
    @wraps("item", result=True)
    def scope_contains(this, item):
        return item in this.__this__
    @attach(Scope, "keys", sign="(this:Scope)->List")
    def scope_keys(this):
        return Object(NativeIterator, __this__=map(context.wrap, this.__this__))
    @attach(Scope, "values", sign="(this:Scope)->List")
    def scope_values(this):
        return Object(NativeIterator, __this__=map(lambda name: this.__this__[name].value, this.__this__))
    @attach(Scope, "items", sign="(this:Scope)->List")
    def scope_items(this):
        return Object(NativeIterator, __this__=map(lambda name: context.wrap((context.wrap(name), this.__this__[name].value)), this.__this__))
    # this will bite me. code.keys? can't use certain names, or they create fake variables
    @attach(Scope, "vars", sign="(this:Scope)->Map")
    def scope_vars(this):
        # TODO: to field
        return context.wrap(this.__this__)
    @attach(Scope, "iter", sign="(this:Scope)->Iterable")
    def map_iter(this):
        return context.call_method(this, "keys")
    @attach(ObjectScope, "__init__", sign="(this:ObjectScope, obj:Object)")
    def object_init(this, obj):
        this.object = obj
    @attach(ObjectScope, "__getattr__", sign="(this:ObjectScope, name:String)->Object")
    @wraps("name")
    @inline_exc(AttributeError)
    def object_getattr(this, name):
        try:
            return context.getattr(this.object, name, inline_exc=True)
        except InlineException:
            pass
        raise InlineException()
    @attach(ObjectScope, "__setattr__", sign="(this:ObjectScope, name:String, value:Object)")
    @wraps("name")
    @inline_exc(AttributeError)
    def object_setattr(this, name, value):
        try:
            return context.setattr(this.object, name, value)
        except AttributeError:
            pass
        raise InlineException()
    @attach(ObjectScope, "declare", sign="(this:ObjectScope, name:String, value:Object, ?type)")
    @wraps("name", "type")
    @inline_exc(AttributeError)
    def object_declare(this, name, value, type=None):
        raise InlineException("cannot declare in object")
    @attach(Module, "__init__", sign="(this:Module, ?path:String, ?file:String)") #
    @wraps("path", "file")
    def module_init(this, path=None, file=None, uproot=False):
        context.call(context.impl(Module.__base__, "__init__"), ([this], {}))
        w_this = context.Wrapper(this)
        w_this.__path__ = path
        w_this.__file__ = os.path.abspath(file) if file else None
    @attach(Module, "__getattr__", sign="(this:Module, name:String)->Object") #
    @wraps("name")
    @inline_exc(AttributeError)
    def module_getattr(this, name):
        if name in this.__this__:
            return this.__this__[name].value
        w_this = context.Wrapper(this)
        if w_this.__path__ is not None:
            try:
                return context.call_method(this, "imp", name)
            except ImportError:
                pass
        raise InlineException()
    @attach(Module, "imp", sign="(this:Module, name:String)->Object")
    @wraps("name")
    @inline_exc(ImportError)
    def module_imp(this, name):
        if name in this.__this__:
            return this.__this__[name].value # weird. otherwise imports delete a module, e.g. code which has all the goodies
        w_this = context.Wrapper(this)
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
            module.__path__ = context.wrap(".".join(path))

            package = context.frame[0] # wat
            with context.FrameContext([package]):
                for package_name in path[:-1]:
                    package = context.getattr(package, package_name)
                    context.frame.append(package)
                context.declare(name, module, context.scope_types.Module)
                context.frame.append(module)
                if filename:
                    context.declare("__file__", context.wrap(filename), String)
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
    @attach(Module, "declare", sign="(this:Module, name:String, value:Object, ?type:Class)")
    @wraps("name")
    def module_declare(this, name, value, type=None):
        w_this = context.Wrapper(this)
        if context.objects.Class in context.inherit_chain(value.__type__):
            qualname = context.unwrap(context.operators.qualname.native(value))
            if qualname is None:
                qualnames = context.scope.get_env().__qualnames__
                context.call_method(qualnames, "__setitem__", value, (w_this.__path__ + "." if w_this.__path__ else "") + name)
        context.call(context.impl(Module.__base__, "declare"), ([this, name, value, type], {}))
    @attach(Env, "__init__", sign="(this:Env)")
    def env_init(this):
        context.call(context.impl(Env.__base__, "__init__"), ([this, ""], {}))
        sources = []
        qualnames = {}
        for name, obj in context.unwrap(context.call_method(this, "builtins")).items():
            # NOTE:
            # builtins do not have special access, their qualnames become invalid if you override them
            # NOTE:
            # declare would use qualname, which would look up the frame[0] Env
            # the purpose of this is to register them here
            if context.objects.Class in context.inherit_chain(obj.__type__):
                qualnames[context.hash(obj)] = name
            this.__this__[name] = Var(obj)

        sources.append(codebase)

        w_this = context.Wrapper(this)
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

def scope_types(context):
    code = context.imp("code")
    declare = context.impl(context.scope_types.Module, "declare")
    def place_types(types_name, module_name=None):
        if module_name is None: module_name = types_name
        module = context.construct(context.scope_types.Module, (["code.{}".format(module_name)], {}))
        context.call(declare, ([code, module_name, module], {}))
        for name, obj in getattr(context, types_name).items():
            context.call(declare, ([module, name, obj], {}))
    place_types("objects")
    place_types("basic_types")
    place_types("operators")
    place_types("node_types")
    place_types("scope_types", "scope")
    place_types("exc_types", "exc")
    place_types("builtins")

def init_scope(context):
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
            # string and ai cause error/loop
        @inline_exc(NameError) # KeyError?
        def __getitem__(self, name):
            for scope in reversed(self.frame):
                impl = context.impl(scope.__type__, "__getattr__")
                if not impl:
                    continue
                try:
                    return context.call(impl, ([scope, name], {})) # , inline_exc=True
                except AttributeError:
                    pass
                if name == "this":
                    if scope.__type__ is context.scope_types.ObjectScope:
                        return scope.object
            raise InlineException("name {} is not defined".format(escape(name)))
        @inline_exc(NameError)
        def __setitem__(self, name, value):
            for scope in reversed(self.frame):
                impl = context.impl(scope.__type__, "__setattr__")
                if not impl:
                    continue
                try:
                    return context.call(impl, ([scope, name, value], {})) # , inline_exc=True
                except AttributeError:
                    pass
                if name == "this":
                    if scope.__type__ is context.scope_types.ObjectScope:
                        raise InlineException("can't set {}".format(escape(name)))
            raise InlineException("name {} is not defined".format(escape(name)))
        def frame_copy(self):
            return self.frame.copy()
            # REASON: closure of signatures, abstracted for setup
        def get_env(self):
            return self.frame[0]
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
    env.name = context.wrap("<env>")
    context.frame.append(env)

def add_ref(context):
    ref = utils.Object()
    context.ref = ref
    def ref_type(path):
        ref[path.split(".")[-1]] = context.imp(path)
    # ref_type("code.iter.IntIterator")
