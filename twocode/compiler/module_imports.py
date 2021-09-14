
def import_module(name, *, filename):
    scope = {}
    exec(compile(f'import {name}', filename, mode='exec'), scope)
    module = scope[name]
    return module
