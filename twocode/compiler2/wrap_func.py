from types import MethodType
import ast
import inspect

def wrap_func_def(func_def, *, filename):
    compiled_func = None
    old_func_def = None
    def patch(func_def: ast.FunctionDef):
        nonlocal compiled_func, old_func_def
        scope = {}
        if isinstance(func_def, ast.Module):
            # TODO: async function def
            func_def = func_def.body[0]
        code = func_def
        code = ast.Module([code], type_ignores=[])
        exec(compile(code, filename, mode='exec'), scope)
        result = scope[func_def.name]
        compiled_func = result
        old_func_def = func_def

    def Func(*args, **kwargs):
        if Func.__2c_source__ is not old_func_def:
            # TODO: replacing __code__ breaks if it has different amount of free vars
            patch(Func.__2c_source__)
        return compiled_func(*args, **kwargs)

    Func.__2c_source__ = func_def

    patch(func_def)
    return Func
