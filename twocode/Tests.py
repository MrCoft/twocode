import inspect
import textwrap

func_gen = lambda f: lambda *args, **kwargs: lambda: f(*args, **kwargs)
def code_arg(name=None):
    raw = "raw" if not name else "raw_" + name
    def wrap(f):
        format = lambda code: textwrap.dedent(code).strip().replace("\t", " " * 4)
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
def auto_cmp(code):
    reflect = str(context.parser.parse(code))
    assert code == reflect, "Expected {}, got {}".format(repr(code), repr(reflect))
@func_gen
@code_arg()
@code_arg("result")
def cmp(code, result):
    reflect = str(context.parser.parse(code))
    assert result == reflect, "Expected {}, got {}".format(repr(result), repr(reflect))
@func_gen
@code_arg()
def fails(code, exc_type_name=None):
    try:
        context.parser.parse(code)
    except Exception as exc:
        if type(exc).__name__ == exc_type_name:
            return
    raise Exception("Expected {} to raise {}".format(repr(code), exc_type_name))
@func_gen
@code_arg()
def compiles(code):
    context.parser.parse(code)
@func_gen
@code_arg()
def parses(code, result):
    tokens = list(context.parser.lexer.parse(code))
    token_types = [token.type for token in tokens]
    assert token_types == result, "Expected {}, got {}".format(result, token_types)
@func_gen
def ast_fails(node_gen, exc_type=None):
    if exc_type is None: exc_type = Exception
    try:
        ast = node_gen(context.parser.node_types)
        context.parser.validate(ast)
    except exc_type:
        return
    raise Exception("Expected node to raise {}".format(exc_type.__name__))
@func_gen
@code_arg()
@code_arg("result")
def evals(code, result):
    obj = context.eval(context.parse(code))
    obj = context.call(context.builtins.repr, ([obj], {}))
    obj = context.unwrap_value(obj)
    assert obj == result, "Expected {}, got {}".format(result, obj)

def name_tests(*args, **kwargs):
    frame, filename, lineno, function, code_context, index = inspect.stack(0)[1]
    module = frame.f_globals
    for i, test in enumerate(args):
        module["test_{}".format(str(i + 1))] = test
    for kw, test in kwargs.items():
        module["test_{}".format(kw)] = test