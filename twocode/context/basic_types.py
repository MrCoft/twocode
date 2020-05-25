from twocode.context.operators import op_assign, op_compare, op_math, op_unary
from twocode import utils
import twocode.utils.string
import builtins
import copy
import textwrap
import re
from twocode.utils.code import type_check
from twocode.utils.interface import preview

literal_eval = {
    "null": lambda value: None,
    "boolean": lambda value: value == "true",
    "integer": lambda value: int(value),
    "float": lambda value: float(value),
    "string": lambda value: value,
}

def add_basic_types(context):
    Class, Func, Arg, BoundMethod = [context.obj[name] for name in "Class, Func, Arg, BoundMethod".split(", ")]
    w, uw, r, dr, op = [context.type_magic[name] for name in "w, uw, r, dr, op".split(", ")]
    wraps = context.native_wraps

    context.basic_types = utils.Object()
    def gen_class(name):
        cls = Class()
        context.basic_types[name] = cls
        return cls
    def attach(cls, name, **kwargs):
        def wrap(func):
            cls.__fields__[name] = Func(native=func, **kwargs)
        return wrap

    Object = gen_class("Object")
    Null = gen_class("Null")

    Bool = gen_class("Bool")
    Float = gen_class("Float")
    Int = gen_class("Int")
    String = gen_class("String")
    List = gen_class("List")
    Array = gen_class("Array")
    Tuple = gen_class("Tuple")
    Map = gen_class("Map")
    Set = gen_class("Set")
    Dynamic = gen_class("Dynamic")

    direct = lambda obj: obj.__this__
    direct_copy = lambda obj: obj.__this__.copy()
    unwrap_map = {
        Null: lambda obj: None,
        Bool: direct,
        Float: direct,
        Int: direct,
        String: direct,
        List: direct_copy,
        Array: direct_copy,
        Tuple: lambda obj: tuple(obj.__this__),
        Map: lambda obj: {uw@ r@ obj._keymap[hash]: obj.__this__[hash] for hash in obj.__this__}, # to param
        Set: direct_copy,
    }
    direct = lambda cls: lambda obj: context.obj.Object(cls, __this__=obj)
    direct_copy = lambda cls: lambda obj: context.obj.Object(cls, __this__=obj.copy())
    wrap_map = {
        builtins.type(None): lambda obj: context.obj.Object(Null),
        bool: direct(Bool),
        float: direct(Float),
        int: direct(Int),
        str: direct(String),
        tuple: lambda obj: context.obj.Object(Tuple, __this__=list(obj)),
        set: direct_copy,
    }
    def wrap_func_list(obj):
        try:
            w_obj = []
            for item in obj:
                type_check(item, context.obj.Ref.Object)
                w_obj.append(item)
            return context.obj.Object(List, __this__=w_obj)
        except TypeError:
            obj_str = context.safe_repr(item)
            error_str = "is a Ref" if isinstance(item, context.obj.Ref) else "isn't wrapped"
            items_str = []
            for item in obj:
                s = context.safe_repr(item)
                s = preview(s, 15, rstrip=True)
                items_str.append(s)
            list_str = iter_str(items_str)
            msg = "error wrapping list [{}], value {} {}".format(list_str, obj_str, error_str)
            raise Exception(msg) from None
    wrap_map[list] = wrap_func_list
    def wrap_func_map(obj):
        try:
            w_obj = {}
            keymap = {}
            for key, value in obj.items():
                type_check(value, context.obj.Ref.Object)
                w_key = w@ key
                hash = op.hash(w_key)
                w_obj[hash] = value
                keymap[hash] = w_key.__refobj__
            return context.obj.Object(Map, __this__=w_obj, _keymap=keymap)
        except TypeError:
            obj_str = context.safe_repr(value)
            key_str = context.safe_repr(w@ key)
            error_str = "is a Ref" if isinstance(value, context.obj.Ref) else "isn't wrapped"
            items_str = []
            for key, value in obj.items():
                key_s = context.safe_repr(w@ key)
                value_s = context.safe_repr(value)
                key_s = preview(key_s, 15, rstrip=True)
                value_s = preview(value_s, 15, rstrip=True)
                s = "{}: {}".format(key_s, value_s)
                items_str.append(s)
            map_str = iter_str(items_str)
            msg = "error wrapping map {{{}}}, value {} at {} {}".format(map_str, obj_str, key_str, error_str)
            raise Exception(msg) from None
    wrap_map[dict] = wrap_func_map
    def iter_str(items_str):
        iter_str = ", ".join(items_str)
        if len(iter_str) >= 63:
            lines = []
            line = ""
            width = 80 - 4
            for i, s in enumerate(items_str):
                if i < len(items_str) - 1:
                    s += ","
                if len(lines) >= 4:
                    line = lines[-1] + " " + s
                    line = preview(line, width, rstrip=True)
                    lines[-1] = line
                    break
                if len(line + " " + s) <= width:
                    if line:
                        line += " "
                    line += s
                else:
                    lines.append(line)
                    line = s
            return "\n{}\n".format("\n".join(" " * 4 + line for line in lines))
        else:
            return iter_str
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
        if isinstance(obj, context.obj.Ref.Object):
            type_check(obj, context.obj.Ref)
        if not isinstance(obj, context.obj.Ref):
            return obj
        # the slot means typing. an object and type...
        cls = context.inherit_chain(obj.__type__)[0]
        if cls in unwrap_map:
            return unwrap_map[cls](obj)
        return obj
    context.unwrap = unwrap
    def wrap(obj):
        lit_type = builtins.type(obj)
        if lit_type in wrap_map:
            return wrap_map[lit_type](obj)
        return obj
    context.wrap = wrap

    def pass_init(cls, default):
        """
            Bool, Float, Int, String have non-null default values
            init constructs all types properly (copy.copy works on floats)
        """
        nullable = hasattr(default, "copy")
        if not nullable:
            @attach(cls, "__default__", return_type=cls) # cls is not a type
            def __default__():
                return context.obj.Object(cls, __this__=copy.copy(default)) # not a type
        @attach(cls, "__init__", args=[Arg("this", cls), Arg("val", Object, default_=context.parse("null"))]) # not a type
        @wraps("val")
        def init(this, val=None):
            if val is None: val = copy.copy(default)
            this.__this__ = val
        # value:Var
        # cls @struct
    pass_init(Bool, False)
    pass_init(Float, 0.0)
    pass_init(Int, 0)
    pass_init(String, "")
    pass_init(List, [])
    pass_init(Array, [])
    pass_init(Tuple, [])
    pass_init(Set, set())
    pass_init(Dynamic, {})
    @attach(Map, "__init__", sign="(this:Map, ?val:Object, **kwargs)")
    @wraps("val")
    def map_init(this, val=None, **kwargs):
        if val is None: val = {}
        this.__this__ = {}
        this._keymap = {}
        for args in val, kwargs:
            for key, value in args.items():
                key = w@ key
                h = op.hash(key)
                this.__this__[h] = value.__refobj__
                this._keymap[h] = key.__refobj__

    def pass_repr(cls, func):
        cls.__fields__["__repr__"] = Func(native=lambda obj: w@ func(obj), args=[Arg("this", cls)], return_type=String)
    pass_repr(Null, lambda obj: "null")
    # object repr to itself
    pass_repr(Bool, lambda obj: "true" if obj.__this__ else "false")
    pass_repr(Float, lambda obj: repr(obj.__this__))
    pass_repr(Int, lambda obj: repr(obj.__this__))
    pass_repr(String, lambda obj: twocode.utils.string.escape(obj.__this__))
    pass_repr(List, lambda obj: "[{}]".format(", ".join(op.repr(r@ item) for item in obj.__this__)))
    pass_repr(Array, lambda obj: "@Array.literal [{}]".format(", ".join(op.repr(r@ item) for item in obj.__this__)))
    pass_repr(Set, lambda obj: "@Set.literal [{}]".format(", ".join(op.repr(r@ item) for item in obj.__this__)))
    @attach(Tuple, "__repr__", sign="(this:Tuple)->String")
    @wraps("this", result=True)
    def tuple_repr(this):
        if not this:
            return "()"
        if len(this) == 1:
            return "({},)".format(op.repr(r@ this[0]))
        else:
            return "({})".format(", ".join(op.repr(r@ item) for item in this))
    @attach(Map, "__repr__", sign="(this:Map)->String")
    @wraps(result=True)
    def map_repr(this):
        if not this.__this__:
            return "Map()"
        return "[{}]".format(", ".join("{}: {}".format(
            op.repr(r@ this._keymap[hash]),
            op.repr(r@ this.__this__[hash]))
        for hash in this.__this__))

    for cls in Bool, Float, Int, String:
        @attach(cls, "__hash__", args=[Arg("this", cls)], return_type=Int)
        @wraps("this", result=True)
        def gen_hash(this):
            return builtins.hash(this)
    @attach(Null, "__hash__", sign="(this:Null)->Int")
    @wraps("this", result=True)
    def null_hash(this):
        raise TypeError("unhashable type: {}".format(twocode.utils.string.escape("Null")))
    # tuple hash - you can't modify keys. it would have to somehow set a copy as the key

    def pass_from(cls):
        def wrap(func):
            cls.__fields__["__from__"] = Func(native=func, args=[Arg("obj", Object)], return_type=cls)
        return wrap
    @pass_from(Object)
    def object_from(obj):
        return obj
    @pass_from(Bool)
    def bool_from(obj):
        return context.operators.bool.native(obj)
    @pass_from(Float)
    @wraps("obj", result=True)
    def float_from(obj):
        if isinstance(obj, int):
            return obj
        raise TypeError()
    @pass_from(String)
    def string_from(obj):
        return context.operators.string.native(obj)

    def pass_bool(cls):
        @attach(cls, "__to__", args=[Arg("obj", cls), Arg("type", context.objects.Class)], return_type=Object)
        @wraps("this", result=True)
        def to(this, cls):
            if cls is Bool:
                return bool(this)
            raise TypeError()
    for cls in Float, Int, String, List, Array, Tuple, Map, Set, Dynamic:
        pass_bool(cls)

    ops = utils.merge_dicts(*(utils.invert_dict(dict) for dict in [op_math, op_compare, op_unary, op_assign]))
    def pass_op(cls, name, b_type=None, return_type=None):
        op = ops[name]
        if b_type:
            code = "context.unwrap(a) {} context.unwrap(b)".format(op)
            def native_op(a, b):
                nonlocal context
                return w@ eval(code)
        else:
            code = "{}context.unwrap(a)".format(op)
            def native_op(a):
                nonlocal context
                return w@ eval(code)
        code = compile(code, "<op>", "eval")
        func = Func(native=native_op)
        func.args = [Arg("a", cls)]
        if b_type:
            func.args.append(Arg("b", b_type))
        func.return_type = return_type
        cls.__fields__["__{}__".format(name)] = func

    for group in [
        utils.redict(op_math, add="+ - * / **".split()),
        utils.redict(op_compare, remove="==".split()),
    ]:
        for symbol, name in group.items():
            pass_op(Float, name, Float, Float)
    for symbol, name in utils.redict(op_unary, remove="~".split()).items():
        pass_op(Float, name, return_type=Float)
    @attach(Float, "__floordiv__", sign="(a:Float, b:Float)->Float")
    @wraps("a", "b", result=True)
    def float_floordiv(a, b):
        return int(a // b)

    for group in [
        utils.redict(op_math, remove="/ ** //".split()),
        utils.redict(op_compare, remove="==".split()),
    ]:
        for symbol, name in group.items():
            pass_op(Int, name, Int, Int)
    for symbol, name in op_unary.items():
        pass_op(Int, name, return_type=Int)

    for cls in Null, Bool, Float, Int, String:
        pass_op(cls, "eq", cls, Bool)

    for cls in String, List, Array, Tuple:
        for args in [
            ("add", cls, cls),
            ("mul", Int, cls),
        ]:
            pass_op(cls, *args)
    for cls in List, Set:
        for args in [
            ("and", cls, cls),
            ("or", cls, cls),
            ("xor", cls, cls),
        ]:
            pass_op(cls, *args)

    @wraps("a", "b", result=True)
    def list_eq(a, b):
        a_len, b_len = len(a), len(b)
        if a_len != b_len:
            return False
        if not a_len:
            return True
        for item1, item2 in zip(a, b):
            if not op.eq(r@ item1, r@ item2):
                return False
        return True
    def pass_eq(cls):
        func = Func(native=list_eq)
        func.args = [Arg("a", cls), Arg("b", cls)]
        func.return_type = Bool
        cls.__fields__["__eq__"] = func
    for cls in List, Array, Tuple:
        pass_eq(cls)
    @attach(Map, "__eq__", sign="(a:Map, b:Map)->Bool")
    @wraps(result=True)
    def map_eq(a, b):
        a_len, b_len = len(a.__this__), len(b.__this__)
        if a_len != b_len:
            return False
        if not a_len:
            return True
        """
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
        """
        # more efficient than repeated operators though?
        for hash in a.__this__:
            if not (hash in a._keymap and hash in b.__this__ and hash in b._keymap):
                return False
            if not op.eq(r@ a._keymap[hash], r@ b._keymap[hash]):
                return False
            if not op.eq(r@ a.__this__[hash], r@ b.__this__[hash], Object):
                return False
        return True
    @attach(Set, "__eq__", sign="(a:Set, b:Set)->Bool")
    @wraps("a", "b", result=True)
    def set_eq(a, b):
        a_len, b_len = len(a), len(b)
        if a_len != b_len:
            return False
        if not a_len:
            return True
        for item in b:
            if not op.eq(r@ a, r@ item):
                return False
        return True

    @attach(List, "__iadd__", sign="(this:List, list:List)")
    @wraps("this", "list")
    def list_iadd(this, list):
        this.extend(list)
    @attach(Map, "__add__", sign="(this:Map, map:Map)->Map")
    @wraps(result=True)
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
        if isinstance(key, context.obj.Ref):
            key = key.__refobj__
        return r@ this.__this__[key]
    @wraps("key")
    def setitem(this, key, value):
        if isinstance(key, context.obj.Ref):
            key = key.__refobj__
        this.__this__[key] = value.__refobj__
    def pass_key(cls, key_type, value_type):
        cls.__fields__["__getitem__"] = Func(native=getitem, args=[
            Arg("this", cls),
            Arg("key", key_type),
        ], return_type=value_type)
        cls.__fields__["__setitem__"] = Func(native=setitem, args=[
            Arg("this", cls),
            Arg("key", key_type),
            Arg("value", value_type),
        ])
    # name -> name<T>
    for cls in List, Array, Tuple:
        pass_key(cls, Int, None)

    #K, V
    @attach(Map, "__getitem__", sign="(this:Map, key)")
    def map_getitem(this, key):
        return r@ this.__this__[op.hash(key)]
    @attach(Map, "__setitem__", sign="(this:Map, key, value)")
    def map_setitem(this, key, value):
        h = op.hash(key)
        this.__this__[h] = value.__refobj__
        this._keymap[h] = key.__refobj__
    # impl
    ###
    @attach(Dynamic, "__getattr__", sign="(this:Dynamic, name:String)->Object")
    @wraps("name")
    def dynamic_getattr(this, name):
        return r@ this.__this__[name]
    @attach(Dynamic, "__setattr__", sign="(this:Dynamic, name:String, value:Object)")
    @wraps("name")
    def dynamic_setattr(this, name, value):
        this.__this__[name] = value.__refobj__

    def pass_method(cls, name, signature, rename=None):
        if rename is None: rename = name
        method = Func(native=lambda this, *args, **kwargs: getattr(this.__this__, name)(*args, **kwargs), sign=signature)
        method.args.insert(0, Arg("this", cls))
        cls.__fields__[rename] = method
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

    @attach(List, "__contains__", sign="(this:List, item)->Bool") # <T>, T
    @wraps("this", result=True)
    def list_contains(this, item):
        # impl of type param?
        for it in this:
            if op.eq(item, r@ it):
                return True
        return False

    @attach(Map, "__contains__", sign="(this:Map, item)->Bool") # <K,V>, K
    @wraps(result=True)
    def map_contains(this, item):
        for it in this._keymap.values():
            if op.eq (item, r@ it):
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
        return context.obj.Object(NativeIterator, __this__=map(lambda hash: w@ (this._keymap[hash], this.__this__[hash]), this.__this__))

    @attach(String, "length", sign="(this:String)->Int")
    @wraps("this", result=True)
    def string_length(this):
        return len(this)
    @attach(List, "length", sign="(this:List)->Int") # <T>
    @wraps("this", result=True)
    def list_length(this):
        return len(this)
    @attach(Map, "length", sign="(this:Map)->Int")
    @wraps("this", result=True) # Map to Dict?
    def map_length(this):
        return len(this._keymap)

    @attach(String, "__getitem__", sign="(this:String, key:Int)->String")
    @wraps("key", result=True)
    def string_getitem(this, key):
        return this.__this__[key]
    @attach(String, "slice", sign="(this:String, pos:Int, ?end:Int)->String")
    @wraps("this", "pos", "end", result=True)
    def string_slice(this, pos, end=None):
        if end is None:
            return this[pos:]
        else:
            return this[pos:end]
    @attach(String, "split", sign="(this:String, sep:String=null)->List<String>")
    @wraps("this", "sep", result=True)
    def string_split(this, sep=None):
        # should be iterator
        ###
        # eventually to an iterator functor thing?
        # IteratorFunc
        return [w@ part for part in this.split(sep)]
    @attach(String, "splitlines", sign="(this:String, keepends:Bool=false)->List<String>")
    @wraps("this", "keepends", result=True)
    def string_splitlines(this, keepends=False):
        return [(w@ part).__refobj__ for part in this.splitlines(keepends)]
    @attach(String, "splitline", sign="(this:String)->String")
    @wraps("this", result=True)
    def string_splitline(this):
        return (w@ line_pattern.match(this)).group()
    line_pattern = re.compile("^(.*)$", re.M)

    @attach(String, "format", sign="(this:String, *args:String, **kwargs:String)->String")
    @wraps("this", result=True)
    def string_format(this, *args, **kwargs):
        args = [op.string(r@ item) for item in args]
        kwargs = {key: op.string(r@ value) for key, value in kwargs.items()}
        # unnecessary conversion once typing works
        return this.format(*args, **kwargs)

    @attach(String, "strip", sign="(this:String)->String")
    @wraps("this", result=True)
    def string_strip(this):
        return this.strip()
    @attach(String, "lstrip", sign="(this:String)->String")
    @wraps("this", result=True)
    def string_lstrip(this):
        return this.lstrip()
    @attach(String, "rstrip", sign="(this:String)->String")
    @wraps("this", result=True)
    def string_rstrip(this):
        return this.rstrip()

    @attach(String, "dedent", sign="(this:String)->String")
    @wraps("this", result=True)
    def string_dedent(this):
        return textwrap.dedent(this)

    @attach(String, "lower", sign="(this:String)->String")
    @wraps("this", result=True)
    def string_lower(this):
        return this.lower()
    @attach(String, "upper", sign="(this:String)->String")
    @wraps("this", result=True)
    def string_upper(this):
        return this.upper()
    @attach(String, "startswith", sign="(this:String, s:String)->Bool")
    @wraps("this", "s", result=True)
    def string_startswith(this, s):
        return this.startswith(s)
    @attach(String, "endswith", sign="(this:String, s:String)->Bool")
    @wraps("this", "s", result=True)
    def string_endswith(this, s):
        return this.endswith(s)
    @attach(String, "ljust", sign='(this:String, width:Int, char:String=" ")->String')
    @wraps("this", "width", "char", result=True)
    def string_ljust(this, width, char=" "):
        return this.ljust(width, char)
    @attach(String, "rjust", sign='(this:String, width:Int, char:String=" ")->String')
    @wraps("this", "width", "char", result=True)
    def string_rjust(this, width, char=" "): # pad, trim
        return this.rjust(width, char)

    @attach(List, "join", sign='(this:List<String>, sep:String=", ")->String')
    @wraps("this", "sep", result=True)
    def list_join(this, sep=", "):
        # should be iterator
        # a time graph - find appropriate scale, show times (0->1.0)
        # 125% of their max
        items = (op.string(r@ item) for item in this)
        return sep.join(items)
    @attach(List, "slice", sign="(this:List<T>, pos:Int, ?end:Int)->List<T>")
    @wraps("this", "pos", "end", result=True)
    def list_slice(this, pos, end=None):
        if end is None:
            return this[pos:]
        else:
            return this[pos:end]
    @attach(List, "from_iter", sign="(iter:Iterable<T>)->List<T>")
    @wraps(result=True)
    def list_from_iter(iter):
        has_next = context.impl(iter.__type__, "has_next")
        next = context.impl(iter.__type__, "next") # op this too?
        has_next = r(context.objects.BoundMethod)@ BoundMethod(iter, has_next)
        next = r(context.objects.BoundMethod)@ BoundMethod(iter, next)
        list = []
        while True:
            cond = uw@ context.call(has_next, ([], {}))
            if not cond:
                break
            item = context.call(next, ([], {}))
            list.append(item.__refobj__)
        return list

    @attach(List, "__iter__", sign="(this:List<T>)->Iterable<T>")
    @wraps("this")
    def list_iter(this):
        return context.obj.Object(NativeIterator, __this__=iter(this))
    # temporary
    @attach(Map, "__iter__", sign="(this:Map<K,V>)->Iterable<K>")
    def map_iter(this):
        return context.call_method(this, "keys")
    @attach(Tuple, "__iter__", sign="(this:Tuple<T>)->Iterable<T>")
    @wraps("this")
    def tuple_iter(this):
        return context.obj.Object(NativeIterator, __this__=iter(this))
    @attach(String, "__iter__", sign="(this:String)->Iterable<String>")
    @wraps("this")
    def string_iter(this):
        return context.obj.Object(NativeIterator, __this__=iter(this))

    NativeIterator = Class()
    context.basic_types.NativeIterator = NativeIterator
    @attach(NativeIterator, "has_next", sign="(this:NativeIterator<T>)->Bool")
    @wraps(result=True)
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
        return r@ this._item
    def unwrap_iter(iter):
        has_next = context.impl(iter.__type__, "has_next")
        next = context.impl(iter.__type__, "next")
        while True:
            if not context.call(has_next, ([iter], {})).__this__:
                break
            yield context.call(next, ([iter], {}))
    context.unwrap_iter = unwrap_iter

# in code.node_types would shorten the paths? or can i do a shady import like this?
