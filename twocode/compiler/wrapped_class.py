from types import MethodType
import ast
import inspect

def wrap_class_def(class_def, *, filename):
    old_class_def = None
    def patch(class_def):
        nonlocal old_class_def
        scope = {}
        print(class_def)
        if isinstance(class_def, ast.Module):
            class_def = class_def.body[0]
        code = class_def
        # if not isinstance(code, ast.Module):
        code = ast.Module([code], type_ignores=[])
        exec(compile(code, filename, mode='exec'), scope)
        instance = scope[class_def.name]
        print(instance, dir(instance), instance.method)
        for name, method in inspect.getmembers(instance, predicate=inspect.isfunction):
            print(method)
            setattr(Cls, name, method)
            # print(method)
        print(instance().method)
        # MethodType(print_classname, None, A)
        old_class_def = class_def

    class Cls:
        __2c_source__ = class_def

        def __new__(cls, *args, **kwargs):
            if Cls.__2c_source__ is not old_class_def:
                # NOTE: Recompile
                patch(Cls.__2c_source__)
            return super(Cls, cls).__new__(cls, *args, **kwargs)

    patch(class_def)
    return Cls
