import sys
import functools

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