import ast
import inspect
import twocode.compiler as tc_compiler


class PythonScope:
    def __init__(self) -> None:
        self.builtins = {}
        self.globals = {}
        self.nonlocals = {}
        self.var_names = set()
        self.filename = None

    @staticmethod
    def from_func(func):
        scope = PythonScope()
        closure = inspect.getclosurevars(func)
        scope.builtins = closure.builtins
        scope.globals = closure.globals
        scope.nonlocals = closure.nonlocals
        edit = tc_compiler.CodeEditor()
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
