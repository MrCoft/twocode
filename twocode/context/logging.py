from twocode import utils
import sys
import re

delim = ".\t".replace("\t", " " * (4 - 1))

def add_logging(context):
    log_default = context.__getattribute__

    class logging(utils.Context):
        def __init__(self, file=None):
            if file is None: file=sys.stderr
            self.file = file
            self.stack_size = 0
        def print(self, msg):
            print(delim * self.stack_size + msg, file=sys.stderr)
        SUPPRESS = "builtins obj".split()
        def getattribute(self, name):
            # NOTE: curiously, a static getattribute receives (context, name) while a method receives only (name,)
            attr = log_default(name)
            if name in logging.SUPPRESS:
                return attr
            if callable(attr):
                return lambda *args, **kwargs: self.func(name, attr, *args, **kwargs)
            self.print(name)
            return attr
        def func(self, name, attr, *args, **kwargs):
            args_str = []
            for arg in args:
                args_str.append(self.obj_str(arg))
            for key, arg in kwargs.items():
                args_str.append("{}={}".format(key, self.obj_str(arg)))
            msg = "{}({})".format(name, ", ".join(args_str))
            self.print(msg)
            try:
                self.stack_size += 1
                return attr(*args, **kwargs)
            finally:
                self.stack_size -= 1
        MAX_OBJ_LEN = 60
        def obj_str(self, obj):
            with ~self:
                s = repr(obj)
            s = s.strip()
            s = re.sub(r'(\r\n|\r|\n)+', "\\n", s)
            s = re.sub(r"\s+", " ", s)
            if len(s) > logging.MAX_OBJ_LEN:
                with ~self:
                    if isinstance(obj, context.obj.Ref):
                        qualname = context.unwrap(context.operators.qualname.native(obj.__type__))
                    else:
                        qualname = type(obj).__name__
                wrap = "{}<{{}}..>".format(qualname)
                s = wrap.format(s[:logging.MAX_OBJ_LEN - len(wrap) + len("{}")])
            return s
        def __enter__(self):
            setattr(type(context), "__getattribute__", self.getattribute)
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            delattr(type(context), "__getattribute__")
    context.logging = logging
