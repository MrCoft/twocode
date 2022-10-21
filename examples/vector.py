import inspect
import ast
import textwrap
import twocode.compiler as tc_compiler


def class_method_decorator(func):
    class ClassMethodDecorator:
        def __init__(self, method) -> None:
            self.method = method

        def __set_name__(self, owner, name):
            return func(self.method, owner)
    return ClassMethodDecorator


class Compiler:
    @staticmethod
    def signature(args):
        def wrap(func):
            edit = tc_compiler.CodeEditor()
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
        edit = tc_compiler.CodeEditor()
        edit.load(func)
        func_code: ast.FunctionDef = edit.code
        scope = edit.get_scope()
        for name, value in list(scope.nonlocals.items()):
            del scope.nonlocals[name]
            free_name = scope.free_name(name)
            value_node = tc_compiler.CodeEditor.create_constant_node(value)
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
    @class_method_decorator
    def expand_constants(func, cls):
        print(func, cls)

        # typing
        # pure analysis
        # replace cascade with values

        # THEN replace ifs and fors

        def is_func_pure(name):
            # go bottom up
            # YES for primitives

            # we need to replace ALL math operations with __add__ etc
            # THEN - we need to figure out types
            # we need to resolve func names to actual functions
            pass
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

        comp = tc_compiler.Compiler()
        comp.add_method(func, cls)
        comp.analyze()

        return func

    @ staticmethod
    def resolve_evals(func):
        # TODO: resolved evals, getattrs and setattrs
        return func

    @staticmethod
    def DCE(func):
        # TODO: remove if False, unused vars
        return func


def dec(x):
    print(x)
    return x


def imdec(f):
    print('imdec', f)
    return f


setattr(imdec, '__set_name__', lambda *args: print('imdec setname', args))


class dec:
    def __init__(self, fn):
        self.fn = fn
        print(fn)

    def __set_name__(self, owner, name):
        setattr(owner, name, self.fn)
        print(owner, name)


class A:
    @imdec
    @dec
    @imdec
    def test(self):
        return 2

    @imdec
    def x(self):
        pass


print(A().test())


def gen_vector(dim, type, *, coords=None):
    class Vector:
        # Compiler.DCE
        # @Compiler.resolve_evals
        @Compiler.expand_constants
        @Compiler.inject_nonlocals
        @Compiler.signature(['x', 'y'])
        def __init__(self, *_, **__):
            if coords:
                if coords:
                    for c in coords:
                        setattr(self, c, eval(c))
    Vector.__name__ = f'{type}{dim}'
    return Vector


Float2 = gen_vector(2, float, coords='xy')

print(ast.unparse(Float2.__init__.__2c_source__))

vec = Float2(1, 2)
print(vec, dir(vec), vec.x)
