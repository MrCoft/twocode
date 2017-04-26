import textwrap

func_gen = lambda f: lambda *args, **kwargs: lambda: f(*args, **kwargs)
def code_arg(f):
    def wrapped(code=None, *args, **kwargs):
        if code:
            code = textwrap.dedent(code).strip().replace("\t", " " * 4)
        if "raw" in kwargs:
            code = kwargs["raw"]
            del kwargs["raw"]
        return f(code, *args, **kwargs)
    return wrapped

def Twocode():
    from twocode.Twocode import Twocode
    return Twocode()
@func_gen
@code_arg
def auto_cmp(code):
    reflect = str(Twocode().parser.parse(code))
    assert code == reflect, "Expected {}, got {}".format(repr(code), repr(reflect))
@func_gen
@code_arg
def cmp(code, result):
    reflect = str(Twocode().parser.parse(code))
    assert result == reflect, "Expected {}, got {}".format(repr(result), repr(reflect))
@func_gen
@code_arg
def fails(code, exc_type=None):
    if exc_type is None: exc_type = Exception
    try:
        Twocode().parser.parse(code)
    except exc_type:
        return
    raise Exception("Expected {} to raise {}".format(repr(code), exc_type.__name__))
@func_gen
@code_arg
def compiles(code):
    Twocode().parser.parse(code)
@func_gen
@code_arg
def parses(code, result):
    tokens = list(Twocode().parser.lexer.parse(code))
    token_types = [token.type for token in tokens]
    assert token_types == result, "Expected {}, got {}".format(result, token_types)
@func_gen
def ast_fails(node_gen, exc_type=None):
    if exc_type is None: exc_type = Exception
    twocode = Twocode()
    try:
        ast = node_gen(twocode.parser.node_types)
        twocode.parser.validate(ast)
    except exc_type:
        return
    raise Exception("Expected node to raise {}".format(exc_type.__name__))
## evals
# execs

parallel = False

def name_tests(name, *args, **kwargs):
    tests = {}
    for i, test in enumerate(args):
        tests["test_{}_{}".format(name, str(i + 1))] = test
    for kw, test in kwargs.items():
        tests["test_{}_{}".format(name, kw)] = test
    return tests

if __name__ == "__main__":
    from utils.UnitTest import unit_test ## port to git

    import twocode.Validators
    unit_test(twocode.Validators)

    import twocode.Exec
    unit_test(twocode.Exec)