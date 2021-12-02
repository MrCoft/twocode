import ast
import inspect
import textwrap
import twocode.compiler as tc_compiler


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
            return tc_compiler.PythonScope.from_func(self.source_func)

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
        scope = tc_compiler.PythonScope.from_func(self.source_func)
        func = scope.eval(self.code)
        return func

    @staticmethod
    def create_constant_node(value):
        value_repr = repr(value)
        node = ast.parse(value_repr, mode='eval', filename='<twocode>')
        node = node.body
        return node
