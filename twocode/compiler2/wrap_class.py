from types import MethodType
import ast
import inspect

def wrap_class_def(class_def, *, filename):
    old_class_def = None
    def patch(class_def):
        nonlocal old_class_def
        scope = {}
        if isinstance(class_def, ast.Module):
            class_def = class_def.body[0]
        code = class_def
        code = ast.Module([code], type_ignores=[])
        exec(compile(code, filename, mode='exec'), scope)
        instance = scope[class_def.name]
        for name, method in inspect.getmembers(instance, predicate=inspect.isfunction):
            setattr(Cls, name, method)
        # MethodType(print_classname, None, A)
        old_class_def = class_def

    class Cls:
        __2c_source__ = None

        def __new__(cls, *args, **kwargs):
            if Cls.__2c_source__ is not old_class_def:
                # NOTE: Recompile
                patch(Cls.__2c_source__)
            return super(Cls, cls).__new__(cls, *args, **kwargs)

    patch(class_def)
    return Cls
