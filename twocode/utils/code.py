import sys
import functools
import inspect

class fail_check:
    def __init__(self, get, check=lambda old, new: old != new, error=lambda: Exception("Check failure")):
        self.get = get
        self.check = check
        self.error = error
        self.old = None
    def __bool__(self):
        new = self.get()
        if self.old is None:
            self.old = new
        else:
            if self.check(self.old, new):
                self.old = new
            else:
                self.old = None
                raise self.error()
        return True

def skip_exc_info(exc_info=None, depth=0):
    if not exc_info:
        exc_info = sys.exc_info()
    exc_type, exc, tb = exc_info
    if depth >= 0:
        for i in range(depth):
            if tb.tb_next:
                tb = tb.tb_next
            else:
                break
    else:
        tbs = []
        while True:
            tbs.append(tb)
            if tb.tb_next:
                tb = tb.tb_next
            else:
                break
        depth = max(-len(tbs), depth)
        tb = tbs[depth]
    return exc_type, exc, tb

def skip_traceback(depth):
    if depth >= 0:
        depth += 1
    def wrap(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            exc_type, exc, tb = None, None, None
            try:
                value = f(*args, **kwargs)
            except:
                exc_type, exc, tb = skip_exc_info(depth=depth)
            if exc:
                internal_exception = exc_type(*exc.args).with_traceback(tb)
                try:
                    raise internal_exception
                finally:
                    tb = internal_exception = None # REASON: gc
            return value
        return wrapped
    return wrap

class InlineException(Exception): pass
def inline_exc(exc_type):
    def wrap(f):
        @functools.wraps(f)
        def wrapped(*args, inline_exc=False, **kwargs):
            if not inline_exc:
                try:
                    return f(*args, **kwargs)
                except InlineException as exc:
                    raise exc_type(*exc.args).with_traceback(exc.__traceback__) from None
                # REASON:
                # - with_traceback makes it point to the source instead of here
                # - from None hides the reraise
            else:
                return f(*args, **kwargs)
        return wrapped
    return wrap

def format_exception_only(exc):
    """
        error message without the traceback or the special SyntaxError treatment
        works exactly like traceback.format_exception(type(exc), exc, None), the code is from there
    """
    exc_type = type(exc)

    stype = exc_type.__qualname__
    smod = exc_type.__module__
    if smod not in ("__main__", "builtins"):
        stype = smod + '.' + stype
    try:
        _str = str(exc)
    except:
        _str = "<unprintable {} object>".format(exc_type.__name__)

    if _str == "None" or not _str:
        line = "{}\n".format(stype)
    else:
        line = "{}: {}\n".format(stype, _str)
    return line

def filter(*fs):
    def f(item):
        for f in fs:
            item = f(item)
        return item
    return f

def map_args(map):
    def wrap(f):
        sign = inspect.signature(f)
        sign = list(sign.parameters.values())
        indices = []
        keywords = set()
        map_args = None
        map_kwargs = None
        arg_names = set()
        for pos, param in enumerate(sign):
            if param.name in map:
                if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    indices.append((param.name, pos))
                    keywords.add(param.name)
                if param.kind == inspect.Parameter.KEYWORD_ONLY:
                    keywords.add(param.name)
                if param.kind == inspect.Parameter.VAR_POSITIONAL:
                    map_args = param.name, pos
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    map_kwargs = param.name
            if param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                arg_names.add(param.name)
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            args = list(args)
            for name, pos in indices:
                if len(args) > pos:
                    args[pos] = map[name](args[pos])
            for name in keywords:
                if name in kwargs:
                    kwargs[name] = map[name](kwargs[name])
            if map_args:
                name, pos = map_args
                args[pos:] = (map[name](item) for item in args[pos:])
            if map_kwargs:
                for name in kwargs:
                    if name not in arg_names:
                        kwargs[name] = map[map_kwargs](kwargs[name])
            return f(*args, **kwargs)
        return wrapped
    return wrap

def type_check(obj, type):
    if not isinstance(obj, type):
        raise TypeError("{} is not {}".format(repr(obj), type.__name__))
    return obj
def type_check_decor(*, result=None, **types):
    def gen_map(type):
        def check(obj):
            type_check(obj, type)
            return obj
        return check
    map = {name: gen_map(type) for name, type in types.items()}
    check_args = map_args(map)
    def wrap(f):
        f = check_args(f)
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            return_value = f(*args, **kwargs)
            if result:
                type_check(return_value, result)
            return return_value
        return wrapped
    return wrap
