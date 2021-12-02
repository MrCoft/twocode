import ast
import inspect
import textwrap
import typing
import twocode.compiler as tc_compiler


class Method:
    def __init__(self, method, cls) -> None:
        self.method = method
        self.cls = cls


class Compiler:
    def __init__(self) -> None:
        self.methods = []
        # type resolution - what stored where?
        pass

    def add_method(self, method, cls):
        self.methods.append(Method(method, cls))

    def add_class(self, cls):
        pass

    def analyze(self) -> None:
        print()
        print("Analyzing...")
        for method in self.methods:
            func = method.method
            edit = tc_compiler.CodeEditor()
            edit.load(func)
            print()
            print(ast.unparse(edit.code))

        print()
        for method in self.methods:
            func = method.method
            edit = tc_compiler.CodeEditor()
            edit.load(func)
            # visitor.visit(edit.code)
            tc_compiler.analysis.print_node_type_counts(edit.code)
            # pyfunctional, pyterator, underscore, fluentttolls

    def to_func_tree():
        # replace math operations
        pass
