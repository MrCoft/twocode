import inspect
import twocode.utils.string
import functools
import textwrap
from twocode.utils.code import format_exception_only
from twocode import utils
import io

def func_gen(f):
    def wrap(*args, **kwargs):
        def wrapped():
            return f(*args, **kwargs)
        return wrapped
    return wrap
def code_arg(name=None):
    raw = "raw" if not name else "raw_" + name
    def wrap(f):
        format = lambda code: twocode.utils.string.dedent(code).strip().replace("\t", " " * 4)
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if not name:
                if args:
                    code = args[0]
                    code = format(code)
                    args = [code] + list(args[1:])
            else:
                if name in kwargs:
                    code = kwargs[name]
                    code = format(code)
                    kwargs[name] = code
            if raw in kwargs:
                code = kwargs[raw]
                if not name:
                    args = [code] + list(args[1:])
                else:
                    kwargs[name] = code
                del kwargs[raw]
            return f(*args, **kwargs)
        return wrapped
    return wrap

from twocode import Twocode
context = Twocode()
# context.declare("T", context.obj.Class())

@func_gen
@code_arg()
@code_arg("result")
def cmp(code, result=None, macro=True):
    if result is None: result = code
    reflect = str(context.parser.parse(code))
    assert context.parser.parser.num_parses == 1, "Parse of {} not unique".format(repr(code))
    assert reflect == result, "Expected {}, got {}".format(repr(result), repr(reflect))
    if not macro:
        return
    code, result = "macro {}".format(code), "macro {}".format(result)
    obj = context.eval(context.parse(code), type="stmt")
    obj = context.shell_repr(obj)
    assert obj == result, "Expected {}, got {}".format(repr(result), repr(obj))
@func_gen
@code_arg()
def fails(code, error=None):
    try:
        context.parse(code)
    except Exception as exc:
        if not error:
            return
        if type(exc).__name__ == error:
            return
        msg = format_exception_only(exc).rstrip()
        if msg == error:
            return
        raise Exception("Expected {} to raise\n{}\ngot\n{}".format(repr(code), textwrap.indent(error, " " * 4), textwrap.indent(msg, " " * 4)))
    raise Exception("Expected {} to raise{}".format(repr(code), "\n{}".format(textwrap.indent(error, " " * 4)) if error else " an exception"))
@func_gen
@code_arg()
def compiles(code):
    context.parse(code)
@func_gen
@code_arg()
def parses(code, result):
    buffer = list(context.parser.lexer.parse(code))
    tokens_repr = " ".join(str(token) for token in buffer)
    assert tokens_repr == result, "Expected {}, got {}".format(result, tokens_repr)
@func_gen
@code_arg()
@code_arg("result")
def evals(code, result=None):
    if result is None: result = code
    obj = context.eval(context.parse(code), type="stmt")
    obj = context.call(context.operators.repr, ([obj], {}))
    obj = context.unwrap(obj)
    assert obj == result, "Expected {}, got {}".format(repr(result), repr(obj))
@func_gen
@code_arg()
def interacts(log):
    assert 1 == 2
    from twocode import Console
    console = Console(context)
    buf = io.StringIO(log)
    buf.seek(0)
    def print_cmp(s):
        result = buf.read(len(s))
        assert s == result, "Expected {}, got {}".format(repr(result), repr(s))
    with utils.Streams(
        stdin=buf,
        stdout=utils.Object(write=print_cmp, flush=lambda: None),
        stderr=utils.Object(write=print_cmp, flush=lambda: None),
    ):
        console.interact()
"""
def interacts(log):
    code_lines = []
    output = io.StringIO()
    def run():
        nonlocal code_lines
        if not code_lines:
            return
        code = "\n".join(code_lines)
        code_lines = []

        with utils.Streams(stdout=buf, stderr=buf):
            obj = context.eval(context.parse(code), type="stmt")
        obj = context.shell_repr(obj)
        if obj is None: obj = ""
        output.append(obj)

    for line in log.splitlines():
        if line.startswith(">>> "):
            run()
            code_lines = [line[4:]]
            output.append(line)
        elif line.startswith("... "):
            code_lines.append(line[4:])
            output.append(line)
    run()

    output = "\n".join(output)
    assert output == log, "\n\n".join(["Expected:", log, "Got:", output])
"""

def name_tests(*args, **kwargs):
    frame, filename, lineno, function, code_context, index = inspect.stack(0)[1]
    module = frame.f_globals
    for i, test in enumerate(args):
        module["test_{}".format(str(i + 1))] = test
    for kw, test in kwargs.items():
        module["test_{}".format(kw)] = test
