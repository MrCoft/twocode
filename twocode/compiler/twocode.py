import ast

import json
import inspect

from .wrap_class import wrap_class_def
from .wrap_func import wrap_func_def
from .module_imports import import_module

class Twocode:
    def __init__(self):
        pass

    def transform_script(self, filename):
        text = open(filename, encoding='utf-8').read()
        code = ast.parse(text, filename, mode='exec')

        d = lambda node: print(ast.dump(node, indent=4))

        context_globals = { __name__: '__main__' }

        for stmt in code.body:
            if isinstance(stmt, ast.ClassDef):
                cls = wrap_func_def(stmt, filename=filename)
                context_globals[stmt.name] = cls
            elif isinstance(stmt, ast.FunctionDef):
                func = wrap_func_def(stmt, filename=filename)
                context_globals[stmt.name] = func
            elif isinstance(stmt, ast.Import):
                # ImportFrom
                for alias in stmt.names:
                    module = import_module(alias.name, filename=filename)
                    asname = alias.name or alias.asname
                    context_globals[asname] = module
            else:
                module_node = ast.Module([stmt], type_ignores=[])
                # print(ast.unparse(module_node))
                # todo: modify stack trace
                exec(compile(module_node, filename, mode='exec'), context_globals, context_globals)
