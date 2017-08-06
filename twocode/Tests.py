import inspect
import twocode.utils.String
import traceback

func_gen = lambda f: lambda *args, **kwargs: lambda: f(*args, **kwargs)
def code_arg(name=None):
    raw = "raw" if not name else "raw_" + name
    def wrap(f):
        format = lambda code: twocode.utils.String.dedent(code).strip().replace("\t", " " * 4)
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

from twocode.Twocode import Twocode
context = Twocode()

@func_gen
@code_arg()
@code_arg("result")
def cmp(code, result=None):
    if result is None: result = code
    reflect = str(context.parser.parse(code))
    assert context.parser.parser.num_parses == 1, "Parse of {} not unique".format(repr(code))
    assert reflect == result, "Expected {}, got {}".format(repr(result), repr(reflect))
    code, result = "macro {}".format(code), "macro {}".format(result)
    obj = context.eval(context.parse(code))
    obj = context.shell_repr(obj)
    print(type(obj), len(repr(obj)))
    # assert obj == result, "Expected {}, got {}".format(repr(result), repr(obj))
    assert obj == result
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
        msg = traceback.format_exception(type(exc), exc, None)
        msg = "".join(msg)
        if msg == error:
            return
    raise Exception("Expected {} to raise {}".format(repr(code), str(error) if error else "an exception"))
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
    obj = context.eval(context.parse(code))
    obj = context.call(context.builtins.repr, ((obj,), {}))
    obj = context.unwrap_value(obj)
    assert obj == result, "Expected {}, got {}".format(repr(result), repr(obj))
@func_gen
@code_arg()
def interacts(log):
    code_lines = []
    output = []
    def run():
        nonlocal code_lines
        if not code_lines:
            return
        code = "\n".join(code_lines)
        code_lines = []

        obj = context.eval(context.parse(code))
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
# prints?

def name_tests(*args, **kwargs):
    frame, filename, lineno, function, code_context, index = inspect.stack(0)[1]
    module = frame.f_globals
    for i, test in enumerate(args):
        module["test_{}".format(str(i + 1))] = test
    for kw, test in kwargs.items():
        module["test_{}".format(kw)] = test