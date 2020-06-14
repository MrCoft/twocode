from typing import List, Optional, Callable, Dict, Any


class Dependency:
    def __init__(self, func: Callable, *, depends: Optional[List[str]] = None, inject: Optional[str] = None):
        self.func = func
        if depends is None:
            depends = []
        if isinstance(depends, str):
            depends = [depends]
        self.depends = depends
        self.inject = inject


setup_funcs: List[Dependency] = []
setup_scope: Dict[str, Any] = {}


def setup(*, depends: Optional[List[str]] = None, inject: Optional[str] = None):
    def wrap(f: Callable):
        setup_funcs.append(Dependency(f, depends=depends, inject=inject))
        return f
    return wrap


def resolve(name: str):
    full_path = name.split('.')
    obj = None
    path_index = 0
    for i in range(len(full_path)):
        path = '.'.join(full_path[:-i])
        if path in setup_scope:
            obj = setup_scope[path]
            path_index = len(full_path) - i
            break
    else:
        return None
    while path_index < len(full_path) and obj is not None:
        obj = getattr(obj, full_path[path_index], None)
    return obj


def complete():
    global setup_funcs
    changed = True
    while changed:
        changed = False
        setup_funcs_re = []
        for obj in setup_funcs:
            depends = [resolve(name) for name in obj.depends]
            if None in depends:
                setup_funcs_re.append(obj)
                changed = True
                continue
            obj.func()
            if obj.inject:
                setup_scope[obj.inject] = resolve(obj.inject)
        setup_funcs = setup_funcs_re
    if setup_funcs:
        buffer = []
        buffer.append('Setup scope:')
        buffer.append(', '.join(setup_scope.keys()))
        buffer.append('')
        buffer.append('Unresolved dependencies:')
        for obj in setup_funcs:
            buffer.append(' ' * 4 + f"{', '.join(obj.depends)} -> {obj.inject}")
        msg = "\n".join(buffer)
        raise Exception(f'Dependency resolution failed:\n\n{msg}')

