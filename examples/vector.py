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

    def get_scope(self):
        if self.source_func is not None:
            return Scope.from_func(self.source_func)

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
        scope = Scope.from_func(self.source_func)
        func = scope.eval(self.code)
        return func

    @staticmethod
    def create_constant_node(value):
        value_repr = repr(value)
        node = ast.parse(value_repr, mode='eval', filename='<twocode>')
        node = node.body
        return node


class Scope:
    def __init__(self) -> None:
        self.builtins = {}
        self.globals = {}
        self.nonlocals = {}
        self.var_names = set()
        self.filename = None

    @staticmethod
    def from_func(func):
        scope = Scope()
        closure = inspect.getclosurevars(func)
        scope.builtins = closure.builtins
        scope.globals = closure.globals
        scope.nonlocals = closure.nonlocals
        edit = CodeEditor()
        edit.load(func)
        scope.var_names = {node.id for node in ast.walk(
            edit.code) if isinstance(node, ast.Name)}
        args = edit.code.args
        for arg_list in [args.posonlyargs, args.args, args.kwonlyargs, [args.vararg, args.kwarg]]:
            for arg in arg_list:
                if arg is None:
                    continue
                scope.var_names.add(arg.arg)
        for outer_scope in [scope.builtins, scope.globals, scope.nonlocals]:
            scope.var_names -= outer_scope.keys()
        scope.filename = inspect.getsourcefile(func)
        return scope

    @property
    def all_used_names(self) -> set[str]:
        names = set()
        names.update(self.builtins.keys())
        names.update(self.globals.keys())
        names.update(self.nonlocals.keys())
        names.update(self.var_names)
        return names

    def free_name(self, name=None):
        names = self.all_used_names
        if name:
            s = name
            num = 1
            while s in names:
                num += 1
                s = f'{name}_{num}'
            return s
        else:
            num = 0
            s = '_0'
            while s in names:
                num += 1
                s = f'_{num}'
            return s

    def eval(self, node):
        scope = {}
        scope.update(self.globals)
        scope['nonlocals'] = self.nonlocals
        args = ast.arguments(
            posonlyargs=[],
            args=[],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[]
        )
        body = [node]

        for name in self.nonlocals.keys():
            assign_node = ast.Assign(targets=[ast.Name(name, ctx=ast.Store())],
                                     value=ast.Subscript(
                value=ast.Name(id='nonlocals', ctx=ast.Load()),
                slice=ast.Constant(value=name),
                ctx=ast.Load())
            )
            body.insert(0, assign_node)

        name = None
        if isinstance(node, ast.FunctionDef):
            name = node.name
        body.append(ast.Return(
            value=ast.Name(id=name, ctx=ast.Load())
        ))

        code = ast.FunctionDef('closure', args, body, decorator_list=[])
        code = ast.Module([code], type_ignores=[])
        ast.fix_missing_locations(code)
        code_obj = compile(code, filename=self.filename, mode='exec')
        exec(code_obj, scope)
        obj = scope['closure']()
        obj.__2c_source__ = node
        return obj


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
    def inject_nonlocals(func):
        edit = CodeEditor()
        edit.load(func)
        func_code: ast.FunctionDef = edit.code
        scope = edit.get_scope()
        for name, value in list(scope.nonlocals.items()):
            del scope.nonlocals[name]
            free_name = scope.free_name(name)
            value_node = CodeEditor.create_constant_node(value)
            assign_node = ast.Assign(
                targets=[ast.Name(id=free_name, ctx=ast.Store())],
                value=value_node
            )
            func_code.body.insert(0, assign_node)

            class RewriteName(ast.NodeTransformer):
                def visit_Name(self, node):
                    if node.id == name:
                        return ast.Name(id=free_name, ctx=node.ctx)
                    else:
                        return node
            RewriteName().visit(func_code)
        new_func = edit.compile_func()
        return new_func

    @staticmethod
    def inline_constants(func):
        # is_var_constant
            # is not an argument
            # is written to once
            # is immutable - not an object, is primitive
            # THEN replace all uses with value
            # if repr is <= 256 chars, we can replace more uses, else keep it
            # inline_constants
        pass

    @staticmethod
    def expand_constants(func):
        # is_func_pure
        # e.g. NO for print
        # YES for list, map, math, boolean expressions
        # @Compiler.pure
        # if method, doesn't modify self
        # doesn't mutate anything

        # is_node_constant
        # is primitive
        # or pure call on constant

        # replace ifs with True or False
        # unroll loops
        return func

    @ staticmethod
    def resolve_evals(func):
        # TODO: resolved evals, getattrs and setattrs
        return func
    
    @staticmethod
    def DCE(func):
        # TODO: remove if False, unused vars
        return func


def gen_vector(dim, type, *, coords=None):
    class Vector:
        # Compiler.DCE
        # @Compiler.resolve_evals
        # @Compiler.expand_constants
        @Compiler.inject_nonlocals
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
print(vec, dir(vec), vec.x)
