import sys
import io
import inspect
import re
import itertools
import random
import os

class Object(dict):
    def __init__(self, **kwargs):
        dict.__init__(self, kwargs)
        self.__dict__ = self
    def __hash__(self):
        return id(self)
    def __getstate__(self):
        return self
    def __setstate__(self, state):
        self.update(state)
        self.__dict__ = self

    def pass_args(self, remove=None):
        if remove is None: remove = []
        frame, filename, lineno, function, code_context, index = inspect.stack(0)[1]
        scope = redict(dict(frame.f_locals), ["__class__", "self"] + remove)
        self.update(scope)

class Context:
    def __init__(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass
    def __call__(self):
        self.__enter__()
    def __invert__(self):
        return reverse_context(self)
class contexts(Context):
    def __init__(self, *contexts):
        self.contexts = list(contexts)
    def __enter__(self):
        for context in self.contexts:
            context.__enter__()
    def __exit__(self, exc_type, exc, tb):
        for context in reversed(self.contexts):
            context.__exit__(exc_type, exc, tb)
class cond_context(Context):
    def __init__(self, cond, context=None, else_context=None):
        self.cond = cond
        self.context = context
        self.else_context = else_context
    def __enter__(self):
        self.leave = None
        if self.cond():
            if self.context:
                self.context.__enter__()
                self.leave = self.context.__exit__
        else:
            if self.else_context:
                self.else_context.__enter__()
                self.leave = self.else_context.__exit__
    def __exit__(self, exc_type, exc, tb):
        if self.leave:
            self.leave(exc_type, exc, tb)
class reverse_context(Context):
    def __init__(self, context):
        self.context = context
    def __enter__(self):
        self.context.__exit__(None, None, None)
    def __exit__(self, exc_type, exc, tb):
        self.context.__enter__()

class Streams(Context):
    def __init__(self, stdin=None, stdout=None, stderr=None):
        self.stdin  = stdin
        self.stdout = stdout
        self.stderr = stderr
    def __enter__(self):
        self.old_stdin  = sys.stdin
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        if self.stdin:	sys.stdin  = self.stdin
        if self.stdout:	sys.stdout = self.stdout
        if self.stderr:	sys.stderr = self.stderr
    def __exit__(self, exc_type, exc, tb):
        sys.stdin  = self.old_stdin
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
def streams_object(streams):
    if streams:
        return Streams(
            streams.stdin,
            streams.stdout,
            streams.stderr
        )
    else:
        return Streams(
            ContentStream(),
            ContentStream(),
            ContentStream()
        )
def wrap_streams(streams, type):
    return Streams(
        type(streams.stdin),
        type(streams.stdout),
        type(streams.stderr),
    )

def conds(*conds):
    return lambda *args, **kwargs: all(cond(*args, **kwargs) for cond in conds if cond)
def gen_cond(gen, cond=None):
    if cond is None:
        cond = lambda val: True
    val = None
    while not val or not cond(val):
        val = gen()
    return val
def hex(n=64, cond=None):
    return gen_cond(lambda: format(random.getrandbits(n), "x"), conds(lambda id: not id.startswith(tuple("0123456789")), cond))

def unique_name(name, scope, suffix_func=lambda n: "_" + str(n)):
    unique_name = name
    n = 2
    while unique_name in scope:
        unique_name = name + suffix_func(n)
        n += 1
    return unique_name

def merge_dicts(*dicts):
    result = {}
    for dict in dicts:
        result.update(dict)
    return result

def redict(d, remove=None, add=None):
    if remove is None: remove = []
    if add is None: add = []
    d = dict(d)
    for var in remove:
        if var in d:
            del d[var]
    if add:
        d = {key: d[key] for key in add if key in d}
    return d

def flatten(iter, depth=1):
    for i in range(depth):
        iter = itertools.chain.from_iterable(iter)
    return list(iter)

def to_pairs(dict):
    return [(key, value) for key, value in dict.items()]
def from_pairs(pairs, sort=None):
    if sort is None:
        sort = lambda list: sorted(list)
    result = {}
    for key, value in pairs:
        if key in result:
            result[key] = sort([result[key], value])[0]
        else:
            result[key] = value
    return result
def invert_pairs(pairs):
    return [(value, key) for key, value in pairs]
def invert_dict(dict, sort=None):
    return from_pairs(invert_pairs(to_pairs(dict)), sort)



def case_path(path, dir=None):
    if dir is None: dir = os.getcwd()
    path = os.path.normpath(path)
    path = path.split(os.sep)
    for name in path[:-1]:
        files = os.listdir(dir)
        if name in files:
            dir = os.path.join(dir, name)
        else:
            dir = None
            break
    if not dir:
        return
    name = path[-1]
    files = os.listdir(dir)
    files = [file for file in files if file.lower() == name.lower()]
    if not files:
        return
    if len(files) > 1:
        raise FileNotFoundError("Found multiple {} files at {}:\n{}{}".format(
            name, dir, " " * 4, " ".join(files)
        ))
    name, ext = os.path.splitext(name)
    file = files[0]
    if not file.startswith(name):
        return
    file = os.path.join(dir, file)
    return file

class Streams(Context):
    def __init__(self, stdin=None, stdout=None, stderr=None):
        self.stdin  = stdin
        self.stdout = stdout
        self.stderr = stderr
    def __enter__(self):
        self.old_stdin  = sys.stdin
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        if self.stdin:	sys.stdin  = self.stdin
        if self.stdout:	sys.stdout = self.stdout
        if self.stderr:	sys.stderr = self.stderr
    def __exit__(self, exc_type, exc, tb):
        sys.stdin  = self.old_stdin
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
def streams_object(streams):
    if streams:
        return Streams(
            streams.stdin,
            streams.stdout,
            streams.stderr
        )
    else:
        return Streams(
            ContentStream(),
            ContentStream(),
            ContentStream()
        )
def wrap_streams(streams, type):
    return Streams(
        type(streams.stdin),
        type(streams.stdout),
        type(streams.stderr),
    )
def streams_encoding(streams, encoding):
    return wrap_streams(streams, lambda stream: io.TextIOWrapper(stream.buffer, encoding=encoding,
                                                                 errors="ignore", line_buffering=True, write_through=True))
class ContentStream:
    def __init__(self, content=""):
        self.content = content
    def detach(self):
        self.content = None
    def read(self, size=-1):
        if size is None or size < 0:
            s = self.content
            self.content = ""
        else:
            s = self.content[:size]
            self.content = self.content[size:]
        return s
    def readline(self, size=-1):
        s = ""
        lines = self.content.splitlines(keepends=True)
        if lines:
            s = lines[0]
            rest = ""
            if size >= 0:
                rest = s[size:]
                s = s[:size]
            self.content = rest + "".join(lines[1:])
        return s
    def write(self, s):
        self.content += s
        return len(s)
    def flush(self):
        pass
class NullStream:
    def __init__(self):
        pass
    def detach(self):
        pass
    def read(self, size=-1):
        return ""
    def readline(self, size=-1):
        return ""
    def write(self, s):
        return len(s)
    def flush(self):
        pass
class FlushStream:
    def __init__(self, stream):
        self.stream = stream
    def detach(self):
        stream = self.stream.detach()
        self.stream = None
        return stream
    def read(self, size=-1):
        return self.stream.read(size)
    def readline(self, size=-1):
        return self.stream.readline(size)
    def write(self, s):
        len = self.stream.write(s)
        self.flush()
        return len
    def flush(self):
        self.stream.flush()



def leading_ws(line):
    return re.match(r"\s*", line).group()
