import inspect
import ast
import textwrap

class Compiler:
    @staticmethod
    def signature(args):
        def wrap(func):
            filename = inspect.getsource(func)
            if hasattr(func, '__2c_source__'):
                source = ast.unparse(func.__2c_source__)
            else:
                source = inspect.getsource(func)
                source = textwrap.dedent(source)
            code = ast.parse(source, mode='exec', filename=filename)
            code: ast.FunctionDef = code.body[0]
            code.decorator_list = []
            code.args = ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg='self'), *map(lambda c: ast.arg(arg=c), args)],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            )
            scope = {}
            code_obj = ast.Module([code], type_ignores=[])
            ast.fix_missing_locations(code_obj)
            code_obj = compile(code_obj, filename=filename, mode='exec')
            exec(code_obj, scope)
            new_func = scope[func.__name__]
            new_func.__2c_source__ = code
            # TODO: transplant nonlocals
            return new_func
        return wrap

    @staticmethod
    def inline_nonlocals(func):
        print(func.__closure__)
        closure = inspect.getclosurevars(func)
        scope = {}
        scope.update(closure.builtins)
        scope.update(closure.globals)
        scope.update(closure.nonlocals)
        print(scope)
        return func

    @staticmethod
    def expand_constants(func):
        # TODO: evaluate constant ifs
        # TODO: expand constant for loops
        return func

    @staticmethod
    def resolve_evals(func):
        # TODO: resolved evals, getattrs and setattrs
        return func

def gen_vector(dim, type, *, coords=None):
    class Vector:
        @Compiler.resolve_evals
        @Compiler.expand_constants
        @Compiler.inline_nonlocals
        @Compiler.signature(['x', 'y'])
        def __init__(self, *_, **__):
            if coords:
                for c in coords:
                    setattr(self, c, eval(c))
    Vector.__name__ = f'{type}{dim}'
    return Vector

Float2 = gen_vector(2, float, coords='xy')

print(ast.unparse(Float2.__init__.__2c_source__))

vec = Float2(1, 2)
print(vec, dir(vec))
