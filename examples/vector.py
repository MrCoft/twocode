import inspect
import ast
import textwrap


class CodeEditor:
    def __init__(self) -> None:
        self.source_func = None
        self.code = None

    @property
    def name(self):
        if self.source_func is not None:
            return self.source_func.__name__

    @property
    def filename(self):
        if self.source_func is not None:
            return inspect.getsourcefile(self.source_func)

    def load(self, obj):
        if inspect.isfunction(obj):
            func = obj
            self.source_func = func
            filename = inspect.getsourcefile(func)
            if hasattr(func, '__2c_source__'):
                source = ast.unparse(func.__2c_source__)
            else:
                source = inspect.getsource(func)
                source = textwrap.dedent(source)
            code = ast.parse(source, mode='exec', filename=filename)
            code: ast.FunctionDef = code.body[0]
            self.code = code

    def compile_func(self):
        scope = {}
        closure = inspect.getclosurevars(self.source_func)
        scope.update(closure.globals)
        scope['nonlocals'] = closure.nonlocals

        code_wrap = ast.FunctionDef('closure', ast.arguments(
            posonlyargs=[],
            args=[],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[]
        ), [
            *map(lambda name: ast.Assign(targets=[ast.Name(name, ctx=ast.Store())],
                                         value=ast.Subscript(
                value=ast.Name(id='nonlocals', ctx=ast.Load()),
                slice=ast.Constant(value=name),
                ctx=ast.Load())
            ), closure.nonlocals.keys()),
            self.code,
            ast.Return(
                value=ast.Name(id=self.name, ctx=ast.Load())
            )
        ], decorator_list=[])

        code_obj = ast.Module([code_wrap], type_ignores=[])
        ast.fix_missing_locations(code_obj)
        code_obj = compile(code_obj, filename=self.filename, mode='exec')
        exec(code_obj, scope)
        new_func = scope['closure']()
        new_func.__2c_source__ = self.code
        return new_func


class Compiler:
    @staticmethod
    def signature(args):
        def wrap(func):
            edit = CodeEditor()
            edit.load(func)
            code: ast.FunctionDef = edit.code
            code.decorator_list = []
            code.args = ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg='self'), *
                      map(lambda c: ast.arg(arg=c), args)],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            )
            new_func = edit.compile_func()
            return new_func
        return wrap

    @staticmethod
    def inline_nonlocals(func):
        edit = CodeEditor()
        edit.load(func)
        code = edit.code
        func_code: ast.FunctionDef = edit.code
        closure = inspect.getclosurevars(func)
        used_names = sorted({node.id for node in ast.walk(
            func_code) if isinstance(node, ast.Name)})
        for name, value in closure.nonlocals.items():
            free_name = 'free_name'

            value_repr = repr(value)
            code = ast.parse(value_repr, mode='eval', filename=edit.filename)
            code = code.body
            assign_node = ast.Assign(
                targets=[ast.Name(id=free_name, ctx=ast.Store())],
                value=code
            )
            func_code.body = [assign_node, *func_code.body]

            class RewriteName(ast.NodeTransformer):
                def visit_Name(self, node):
                    if node.id == name:
                        return ast.Name(id=free_name, ctx=node.ctx)
                    else:
                        return node
            RewriteName().visit(func_code)
        new_func = edit.compile_func()
        return new_func

    @ staticmethod
    def expand_constants(func):
        # TODO: evaluate constant ifs
        # TODO: expand constant for loops
        return func

    @ staticmethod
    def resolve_evals(func):
        # TODO: resolved evals, getattrs and setattrs
        return func


def gen_vector(dim, type, *, coords=None):
    class Vector:
        # @Compiler.resolve_evals
        # @Compiler.expand_constants
        @ Compiler.inline_nonlocals
        @ Compiler.signature(['x', 'y'])
        def __init__(self, *_, **__):
            if coords:
                for c in coords:
                    setattr(self, c, eval(c))
    Vector.__name__ = f'{type}{dim}'
    return Vector


Float2 = gen_vector(2, float, coords='xy')

print(ast.unparse(Float2.__init__.__2c_source__))

vec = Float2(1, 2)
print(vec, dir(vec), vec.x)
