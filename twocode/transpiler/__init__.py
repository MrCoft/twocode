from twocode.lang.parser import Parser
import builtins
from twocode.parser import Console as ConsoleBase
from twocode.transpiler.native.code import map_twocode_to_native, native_source
import sys
from twocode.transpiler.context import Twocode

def tree_str(node):
    node_type = builtins.type(node)
    type_name = node_type.__name__
    if node is None:
        return str(node)
    return node.str_func(delim=".\t".replace("\t", " " * (4 - 1)), str=tree_str)

class Console(ConsoleBase):
    def __init__(self, context=None):
        super().__init__()
        self.context = Twocode()
        self.parser = Parser()
        self.compile = lambda code: self.parser.parse(code)
    # @twocode.utils.code.skip_traceback(0)
    def run(self, code):
        ast = self.compile(code)
        if ast is None:
            return True
        try:
            print(tree_str(ast))
            native_code = map_twocode_to_native((ast))
            print(native_code)
            source = native_source(native_code)
            print(source)
            self.context.eval(source)
            pass # obj = self.context.eval(ast, type="stmt")
        except Exception as exc:
            # msg = self.context.traceback(exc)
            print(exc, file=sys.stderr)
            return False
        if self.shell:
            try:
                pass # obj = self.context.shell_repr(obj)
            except Exception as exc:
                # msg = self.context.internal_error_msg(exc)
                # msg = " " * 4 + code.splitlines()[-1] + msg
                print(exc, file=sys.stderr)
                return False
            # if obj is not None:
            #     print(obj, file=sys.stderr, flush=True)
            # print(ast)
        return False
    def eval(self, code):
        with self.context():
            ast = self.compile(code)
            return self.context.eval(ast, type="expr")
    def exec(self, code):
        with self.context():
            ast = self.compile(code)
            self.context.eval(ast, type="stmt")


if __name__ == "__main__":
    console = Console()
    console.interact()
