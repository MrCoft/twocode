import sys
import io

class Context:
    def __init__(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        pass
    def __call__(self):
        self.__enter__()
class contexts(Context):
    def __init__(self, *contexts):
        self.contexts = list(contexts)
    def __enter__(self):
        for context in self.contexts:
            context.__enter__()
    def __exit__(self, type, value, traceback):
        for context in reversed(self.contexts):
            context.__exit__(type, value, traceback)
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
    def __exit__(self, type, value, traceback):
        if self.leave:
            self.leave(type, value, traceback)

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

def free_var(var, scope):
    free_var = var
    n = 2
    while free_var in scope:
        free_var = var + str(n)
        n += 1
    return free_var


def conds(*conds):
    return lambda *args, **kwargs: all(cond(*args, **kwargs) for cond in conds if cond)
def gen_cond(gen, cond=None):
    if cond is None:
        cond = lambda val: True
    val = None
    while not val or not cond(val):
        val = gen()
    return val
def hex_id(n=64, cond=None):
    return gen_cond(lambda: hex(n), conds(lambda id: not id.startswith(tuple("0123456789")), cond))


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
    def __exit__(self, type, value, traceback):
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