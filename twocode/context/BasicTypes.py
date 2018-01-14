from twocode.context.Operators import op_assign, op_compare, op_math, op_unary
from twocode import Utils
import twocode.utils.String
import builtins
import copy
import textwrap

def add_basics(context):
    Class, Func, Arg = [context.obj[name] for name in "Class Func Arg".split()]
    wraps = context.native_wraps

    context.basic_types = Utils.Object()
    def gen_type(name):
        type = context.obj.Class()
        context.basic_types[name] = type
        return type
    def attach(type, name, **kwargs):
        def wrap(func):
            type.__fields__[name] = Func(native=func, **kwargs)
        return wrap

    Null = gen_type("Null")
    Dynamic = gen_type("Dynamic")

    Bool = gen_type("Bool")
    Float = gen_type("Float")
    Int = gen_type("Int")
    String = gen_type("String")
    List = gen_type("List")
    Array = gen_type("Array")
    Tuple = gen_type("Tuple")
    Map = gen_type("Map")
    Set = gen_type("Set")

    direct = lambda obj: obj.__this__
    unwrap_map = {
        Null: lambda obj: None,
        Bool: direct,
        Float: direct,
        Int: direct,
        String: direct,
        List: direct,
        Array: direct,
        Tuple: lambda obj: tuple(obj.__this__),
        Map: lambda obj: {context.unwrap(obj._keymap[hash]): obj.__this__[hash] for hash in obj.__this__},
        Set: direct,
    }
    direct = lambda type: lambda obj: context.obj.Object(type, __this__=obj)
    wrap_map = {
        builtins.type(None): lambda obj: context.obj.Object(Null),
        bool: direct(Bool),
        float: direct(Float),
        int: direct(Int),
        str: direct(String),
        list: direct(List),
        tuple: lambda obj: context.obj.Object(Tuple, __this__=list(obj)),
        dict: lambda obj: context.obj.Object(Map,
                                             __this__={context.hash(context.wrap(key)): obj[key] for key in obj},
                                             _keymap={context.hash(context.wrap(key)): context.wrap(key) for key in obj},
                                             ),
        set: direct(Set),
    }
    """
        REASON:
        the wraps' purpose is to call them on objects that might or might not be wrapped
        unwrapping isn't deep
            you never unwrap large structures
        used by context to create literals

        OLD DESIGN:
        unwrapping was automatic for all native functions
        this made it impossible to define assignments
        solved by making it optional, decorate with @wraps

        INIT PROBLEM:
        a basic type's __this__ is defined on __init__
        but that is called in a new scope, an ObjectScope
        whose native __init__ fails unwrapping an undefined object

        ABSTRACT PROBLEM:
        child types might introduce new variables
        but base implementations still only want to see the unwrapped __this__
    """

    def unwrap(obj):
        if not hasattr(obj, "__type__"):
            return obj
        # the slot means typing. an object and type...
        type = context.inherit_chain(obj.__type__)[0]
        if type in unwrap_map:
            return unwrap_map[type](obj)
        return obj
    context.unwrap = unwrap
    def wrap(obj):
        lit_type = builtins.type(obj)
        if lit_type in wrap_map:
            return wrap_map[lit_type](obj)
        return obj
    context.wrap = wrap
    class Wrapper:
        def __init__(self, obj):
            self.__dict__["obj"] = obj
        def __getattr__(self, name):
            return context.unwrap(self.obj[name])
        def __setattr__(self, name, value):
            self.obj[name] = context.wrap(value)
    context.Wrapper = Wrapper

    def pass_init(type, default):
        """
            Bool, Float, Int, String have non-null default values
            init constructs all types properly (copy.copy works on floats)
        """
        nullable = hasattr(default, "copy")
        if not nullable:
            @attach(type, "__default__", return_type=type)
            def __default__():
                return context.obj.Object(type, __this__=default)
        @attach(type, "__init__", args=[Arg("this", type), Arg("val", Dynamic, default_=context.parse("null"))])
        @wraps("val")
        def init(this, val=None):
            if val is None: val = copy.copy(default)
            this.__this__ = val
        # value:Var
        # cls @struct
    pass_init(Dynamic, {})
    pass_init(Bool, False)
    pass_init(Float, 0.0)
    pass_init(Int, 0)
    pass_init(String, "")
    pass_init(List, [])
    pass_init(Array, [])
    pass_init(Tuple, [])
    pass_init(Set, set())
    @attach(Map, "__init__", sign="(this:Map, ?val:Dynamic, **kwargs)")
    @wraps("val")
    def map_init(this, val=None, **kwargs):
        if val is None: val = {}
        this.__this__ = {}
        this._keymap = {}
        for args in val, kwargs:
            for key, value in args.items():
                key = context.wrap(key)
                h = context.hash(key)
                this.__this__[h] = value
                this._keymap[h] = key

    def pass_repr(type, func):
        type.__fields__["repr"] = Func(native=lambda obj: context.wrap(func(obj)), args=[Arg("this", type)], return_type=String)
    pass_repr(Null, lambda obj: "null")
    # dynamic repr to itself
    pass_repr(Bool, lambda obj: "true" if obj.__this__ else "false")
    pass_repr(Float, lambda obj: repr(obj.__this__))
    pass_repr(Int, lambda obj: repr(obj.__this__))
    pass_repr(String, lambda obj: twocode.utils.String.escape(obj.__this__))
    pass_repr(List, lambda obj: "[{}]".format(", ".join(context.unwrap(context.operators.repr.native(item)) for item in obj.__this__)))
    pass_repr(Array, lambda obj: "@Array.literal [{}]".format(", ".join(context.unwrap(context.operators.repr.native(item)) for item in obj.__this__)))
    pass_repr(Set, lambda obj: "@Set.literal [{}]".format(", ".join(context.unwrap(context.operators.repr.native(item)) for item in obj.__this__)))
    @attach(Tuple, "repr", sign="(this:Tuple)->String")
    @wraps("this", wrap_return=True)
    def tuple_repr(this):
        if not this:
            return "()"
        if len(this) == 1:
            return "({},)".format(context.unwrap(context.operators.repr.native(this[0])))
        else:
            return "({})".format(", ".join(context.unwrap(context.operators.repr.native(item)) for item in this))
    @attach(Map, "repr", sign="(this:Map)->String")
    @wraps(wrap_return=True)
    def map_repr(this):
        if not this.__this__:
            return "Map()"
        return "[{}]".format(", ".join("{}: {}".format(
            context.unwrap(context.operators.repr.native(this._keymap[hash])),
            context.unwrap(context.operators.repr.native(this.__this__[hash])))
        for hash in this.__this__))

    for type in Bool, Float, Int, String:
        @attach(type, "hash", args=[Arg("this", type)], return_type=Int)
        @wraps("this", wrap_return=True)
        def gen_hash(this):
            return builtins.hash(this)
    @attach(Null, "hash", sign="(this:Null)->Int")
    @wraps("this", wrap_return=True)
    def null_hash(this):
        raise TypeError("unhashable type: {}".format(repr("Null")))
    # tuple hash - you can't modify keys. it would have to somehow set a copy as the key

    def pass_from(type):
        def wrap(func):
            type.__fields__["__from__"] = Func(native=func, args=[Arg("obj", Dynamic)], return_type=type)
        return wrap
    @pass_from(Dynamic)
    def dynamic_from(obj):
        return obj
    @pass_from(Bool)
    def bool_from(obj):
        return context.operators.bool.native(obj)
    @pass_from(Float)
    @wraps("obj", wrap_return=True)
    def float_from(obj):
        if isinstance(obj, int):
            return obj
        raise TypeError()
    @pass_from(String)
    def string_from(obj):
        return context.operators.string.native(obj)

    ops = Utils.merge_dicts(*(Utils.invert_dict(dict) for dict in [op_math, op_compare, op_unary, op_assign]))
    def pass_op(type, name, b_type=None, return_type=None):
        op = ops[name]
        func = Func(native=(lambda a, b: context.wrap(eval("context.unwrap(a) {} context.unwrap(b)".format(op)))) if b_type else lambda a: context.wrap(eval("{}context.unwrap(a)".format(op))))
        func.args = [Arg("a", type)]
        if b_type:
            func.args.append(Arg("b", b_type))
        func.return_type = return_type
        type.__fields__["__{}__".format(name)] = func

    for group in [
        Utils.redict(op_math, add="+ - * / **".split()),
        Utils.redict(op_compare, remove="==".split()),
    ]:
        for symbol, name in group.items():
            pass_op(Float, name, Float, Float)
    for symbol, name in Utils.redict(op_unary, remove="~".split()).items():
        pass_op(Float, name, return_type=Float)
    @attach(Float, "__floordiv__", sign="(a:Float, b:Float)->Float")
    @wraps("a", "b", wrap_return=True)
    def float_floordiv(a, b):
        return int(a // b)

    for group in [
        Utils.redict(op_math, remove="/ ** //".split()),
        Utils.redict(op_compare, remove="==".split()),
    ]:
        for symbol, name in group.items():
            pass_op(Int, name, Int, Int)
    for symbol, name in op_unary.items():
        pass_op(Int, name, return_type=Int)

    for type in Null, Bool, Float, Int, String:
        pass_op(type, "eq", type, Bool)

    for type in String, List, Array, Tuple:
        for args in [
            ("add", type, type),
            ("mul", Int, type),
        ]:
            pass_op(type, *args)
    for type in List, Set:
        for args in [
            ("and", type, type),
            ("or", type, type),
            ("xor", type, type),
        ]:
            pass_op(type, *args)

    @wraps("a", "b", wrap_return=True)
    def list_eq(a, b):
        a_len, b_len = len(a), len(b)
        if a_len != b_len:
            return False
        if not a_len:
            return True
        impl = context.impl(a[0].__type__, "__eq__")
        if impl:
            cmp = lambda a, b: context.unwrap(context.call(impl, ([a, b], {})))
        else:
            cmp = lambda a, b: a is b
        for item1, item2 in zip(a, b):
            if not cmp(item1, item2):
                return False
        return True
    def pass_eq(type):
        func = Func(native=list_eq)
        func.args = [Arg("a", type), Arg("b", type)]
        func.return_type = Bool
        type.__fields__["__eq__"] = func
    for type in List, Array, Tuple:
        pass_eq(type)
    @attach(Map, "__eq__", sign="(a:Map, b:Map)->Bool")
    @wraps(wrap_return=True)
    def map_eq(a, b):
        a_len, b_len = len(a.__this__), len(b.__this__)
        if a_len != b_len:
            return False
        if not a_len:
            return True
        item = next(iter(a._keymap.values()))
        impl_keys = context.impl(item.__type__, "__eq__")
        if impl_keys:
            cmp_keys = lambda a, b: context.unwrap(context.call(impl_keys, ([a, b], {})))
        else:
            cmp_keys = lambda a, b: a is b
        item = next(iter(a.__this__.values()))
        impl_values = context.impl(item.__type__, "__eq__")
        if impl_values:
            cmp_values = lambda a, b: context.unwrap(context.call(impl_values, ([a, b], {})))
        else:
            cmp_values = lambda a, b: a is b
        for hash in a.__this__:
            if not (hash in a._keymap and hash in b.__this__ and hash in b._keymap):
                return False
            if not cmp_keys(a._keymap[hash], b._keymap[hash]):
                return False
            if not cmp_values(a.__this__[hash], b.__this__[hash]):
                return False
        return True
    @attach(Set, "__eq__", sign="(a:Set, b:Set)->Bool")
    @wraps("a", "b", wrap_return=True)
    def set_eq(a, b):
        a_len, b_len = len(a), len(b)
        if a_len != b_len:
            return False
        if not a_len:
            return True
        impl = context.impl(a.__type__, "contains")
        for item in b:
            if not context.unwrap(context.call(impl, ([a, item], {}))):
                return False
        return True

    @attach(List, "__iadd__", sign="(this:List, list:List)")
    @wraps("this", "list")
    def list_iadd(this, list):
        this.extend(list)
    @attach(Map, "__add__", sign="(this:Map, map:Map)->Map")
    @wraps(wrap_return=True)
    def map_add(this, map):
        copy = context.obj.Object(Map, __this__=this.__this__.copy(), _keymap=this._keymap.copy())
        copy.__this__.update(map.__this__)
        copy._keymap.update(map._keymap)
        return copy
    @attach(Map, "__iadd__", sign="(this:Map, map:Map)")
    def map_iadd(this, map):
        this.__this__.update(map.__this__)
        this._keymap.update(map._keymap)
    @attach(Set, "__iand__", sign="(this:Set, set:Set)")
    @wraps("this", "set")
    def set_iand(this, set):
        this.update(set)

    @wraps("key")
    def getitem(this, key):
        return this.__this__[key]
    @wraps("key")
    def setitem(this, key, value):
        this.__this__[key] = value
    def pass_key(type, key_type, value_type):
        type.__fields__["__getitem__"] = Func(native=getitem, args=[
            Arg("this", type),
            Arg("key", key_type),
        ], return_type=value_type)
        type.__fields__["__setitem__"] = Func(native=setitem, args=[
            Arg("this", type),
            Arg("key", key_type),
            Arg("value", value_type),
        ])
    # name -> name<T>
    for type in List, Array, Tuple:
        pass_key(type, Int, None)

    #K, V
    @attach(Map, "__getitem__", sign="(this:Map, key)")
    def map_getitem(this, key):
        return this.__this__[context.hash(key)]
    @attach(Map, "__setitem__", sign="(this:Map, key, value)")
    def map_setitem(this, key, value):
        h = context.hash(key)
        this.__this__[h] = value
        this._keymap[h] = key
    # impl
    ###
    @attach(Dynamic, "__getattribute__", sign="(this:Dynamic, name:String)->Dynamic")
    @wraps("this", "name")
    def dynamic_getattribute(this, name):
        return this.__this__[name]
    @attach(Dynamic, "__getattribute__", sign="(this:Dynamic, name:String, value:Dynamic)")
    @wraps("this", "name")
    def dynamic_setattribute(this, name, value):
        this.__this__[name] = value

    def pass_method(type, name, signature, rename=None):
        if rename is None: rename = name
        method = Func(native=lambda this, *args, **kwargs: getattr(this.__this__, name)(*args, **kwargs), sign=signature)
        method.args.insert(0, Arg("this", type))
        type.__fields__[rename] = method
    for args in """
        format (*iter:Iter<String>)->String
        join (iter:Iter<String>)->String
    """.strip().splitlines():
        pass_method(String, *args.split())
    for args in """
        append (item) push
    """.strip().splitlines(): # ->T?
        pass_method(List, *args.split())
    for args in """
        keys ()->List
        values ()->List
        items ()->List
    """.strip().splitlines(): # <K> <V> <Tuple<K,V>>
        pass_method(Map, *args.split())

    @attach(List, "contains", sign="(this:List, item)->Bool") # <T>, T
    @wraps("this", wrap_return=True)
    def list_contains(this, item):
        # impl of type param?
        impl = context.impl(item.__type__, "__eq__")
        if impl:
            cmp = lambda a, b: context.unwrap(context.call(impl, ([a, b], {})))
        else:
            cmp = lambda a, b: a is b
        for it in this:
            if cmp(it, item):
                return True
        return False

    @attach(Map, "contains", sign="(this:Map, item)->Bool") # <K,V>, K
    @wraps(wrap_return=True)
    def map_contains(this, item):
        # impl of type param?
        impl = context.impl(item.__type__, "__eq__")
        if impl:
            cmp = lambda a, b: context.unwrap(context.call(impl, ([a, b], {})))
        else:
            cmp = lambda a, b: a is b
        for it in this._keymap.values():
            if cmp(it, item):
                return True
        return False

    @attach(Map, "keys", sign="(this:Map)->List") #<K, V> <K>
    def map_keys(this):
        return context.obj.Object(NativeIterator, __this__=iter(this._keymap.values()))
    @attach(Map, "values", sign="(this:Map)->List<V>") # <K,V> <V>
    def map_values(this):
        return context.obj.Object(NativeIterator, __this__=iter(this.__this__.values()))
    @attach(Map, "items", sign="(this:Map)->Iter<Tuple>") # <K,V>
    # <K,V>
    def map_items(this):
        return context.obj.Object(NativeIterator, __this__=map(lambda hash: context.wrap((this._keymap[hash], this.__this__[hash])), this.__this__))

    @attach(List, "length", sign="(this:List)->Int") # <T>
    @wraps("this", wrap_return=True)
    def list_length(this):
        return len(this)

    @attach(String, "length", sign="(this:String)->Int")
    @wraps("this", wrap_return=True)
    def string_length(this):
        return len(this)



    @wraps("key")
    def getitem(this, key):
        return this.__this__[key]
    @wraps("key")
    def setitem(this, key, value):
        this.__this__[key] = value
    def pass_key(type, key_type, value_type):
        type.__fields__["__getitem__"] = Func(native=getitem, args=[
            Arg("this", type),
            Arg("key", key_type),
        ], return_type=value_type)
        type.__fields__["__setitem__"] = Func(native=setitem, args=[
            Arg("this", type),
            Arg("key", key_type),
            Arg("value", value_type),
        ])
    # name -> name<T>
    for type in List, Array, Tuple:
        pass_key(type, Int, None)

    @attach(String, "__getitem__", sign="(this:String, key:Int)->String")
    @wraps("key", wrap_return=True)
    def string_getitem(this, key):
        return this.__this__[key]

    @attach(String, "split", sign="(this:String, sep:String=null)->List<String>")
    @wraps("this", "sep", wrap_return=True)
    def string_split(this, sep=None):
        # should be iterator
        ###
        # eventually to an iterator functor thing?
        # IteratorFunc
        return [context.wrap(part) for part in this.split(sep)]
    @attach(String, "splitlines", sign="(this:String, keepends:Bool=false)->List<String>")
    @wraps("this", "keepends", wrap_return=True)
    def string_splitlines(this, keepends=False):
        return [context.wrap(part) for part in this.splitlines(keepends)]

    @attach(String, "format", sign="(this:String, *args:String, **kwargs:String)->String")
    @wraps("this", wrap_return=True)
    def string_format(this, *args, **kwargs):
        args = [context.unwrap(context.operators.string.native(item)) for item in args]
        kwargs = {key: context.unwrap(context.operators.string.native(value)) for key, value in kwargs.items()}
        # unnecessary conversion once typing works
        return this.format(*args, **kwargs)

    @attach(String, "strip", sign="(this:String)->String")
    @wraps("this", wrap_return=True)
    def string_strip(this):
        return this.strip()
    @attach(String, "lstrip", sign="(this:String)->String")
    @wraps("this", wrap_return=True)
    def string_lstrip(this):
        return this.lstrip()
    @attach(String, "rstrip", sign="(this:String)->String")
    @wraps("this", wrap_return=True)
    def string_rstrip(this):
        return this.rstrip()

    @attach(String, "dedent", sign="(this:String)->String")
    @wraps("this", wrap_return=True)
    def string_dedent(this):
        return textwrap.dedent(this)

    @attach(String, "lower", sign="(this:String)->String")
    @wraps("this", wrap_return=True)
    def string_lower(this):
        return this.lower()
    @attach(String, "upper", sign="(this:String)->String")
    @wraps("this", wrap_return=True)
    def string_upper(this):
        return this.upper()
    @attach(String, "startswith", sign="(this:String, s:String)->Bool")
    @wraps("this", "s", wrap_return=True)
    def string_startswith(this, s):
        return this.startswith(s)
    @attach(String, "endswith", sign="(this:String, s:String)->Bool")
    @wraps("this", "s", wrap_return=True)
    def string_endswith(this, s):
        return this.endswith(s)

    @attach(List, "join", sign='(this:List<String>, sep:String=", ")->String')
    @wraps("this", "sep", wrap_return=True)
    def list_join(this, sep=", "):
        # should be iterator
        # a time graph - find appropriate scale, show times (0->1.0)
        # 125% of their max
        items = (context.unwrap(context.operators.string.native(item)) for item in this)
        return sep.join(items)
    @attach(List, "slice", sign="(this:List<T>, pos:Int, ?end:Int)->List<T>")
    @wraps("this", "pos", "end", wrap_return=True)
    def list_slice(this, pos, end=None):
        if end is not None:
            return this[pos:]
        else:
            return this[pos:end]
    @attach(List, "from_iter", sign="(iter:Iterable<T>)->List<T>")
    @wraps(wrap_return=True)
    def list_from_iter(iter):
        has_next = context.impl(iter.__type__, "has_next")
        next = context.impl(iter.__type__, "next")
        has_next = context.obj.BoundMethod(iter, has_next)
        next = context.obj.BoundMethod(iter, next)
        list = []
        while True:
            cond = context.call(has_next, ([], {}))
            cond = context.unwrap(cond)
            if not cond:
                break
            item = context.call(next, ([], {}))
            list.append(item)
        return list

    @attach(List, "iter", sign="(this:List<T>)->Iterable<T>")
    @wraps("this")
    def list_iter(this):
        return context.obj.Object(NativeIterator, __this__=iter(this))
    # temporary
    @attach(Map, "iter", sign="(this:Map<K,V>)->Iterable<K>")
    def map_iter(this):
        return context.call_method(this, "keys")

    NativeIterator = context.obj.Class()
    context.basic_types.NativeIterator = NativeIterator
    @attach(NativeIterator, "has_next", sign="(this:NativeIterator<T>)->Bool")
    def nativeiterator_has_next(this):
        try:
            this._item = next(this.__this__)
        except StopIteration:
            this._item = None
            return False
        else:
            return True
    @attach(NativeIterator, "next", sign="(this:NativeIterator)") #T
    def nativeiterator_next(this):
        return this._item
# in code.node_types would shorten the paths? or can i do a shady import like this?