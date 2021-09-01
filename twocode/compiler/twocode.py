import ast

import json
import inspect

from .wrapped_class import wrap_class_def

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
                cls = wrap_class_def(stmt, filename=filename)
                context_globals[stmt.name] = cls
            elif isinstance(stmt, ast.FunctionDef):
                pass
            else:
                module_node = ast.Module([stmt], type_ignores=[])
                print(ast.unparse(module_node))
                # todo: modify stack trace
                exec(compile(module_node, filename, mode='exec'), context_globals, context_globals)
