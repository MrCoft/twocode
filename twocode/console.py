from twocode.parser import Console as ConsoleBase
import sys
import twocode.utils.code

class Console(ConsoleBase):
    def __init__(self, context=None):
        super().__init__()
        from twocode import Twocode
        if context is None: context = Twocode()
        self.context = context
        self.compile = lambda code: self.context.parse(code)
    @twocode.utils.code.skip_traceback(0)
    def run(self, code):
        ast = self.compile(code)
        if ast is None:
            return True
        try:
            obj = self.context.eval(ast, type="stmt")
        except Exception as exc:
            msg = self.context.traceback(exc)
            print(msg, file=sys.stderr)
            return False
        if self.shell:
            try:
                obj = self.context.shell_repr(obj)
            except Exception as exc:
                msg = self.context.internal_error_msg(exc)
                msg = " " * 4 + code.splitlines()[-1] + msg
                print(msg, file=sys.stderr)
                return False
            if obj is not None:
                print(obj, file=sys.stderr, flush=True)
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
    #import bprofile
    #with bprofile.BProfile("profile.png"):

    #import time
    #start = time.time()

    console = Console()
    context = console.context

    # print("open")
    # start = time.time()

    # context.imp("test_js")

    # print(time.time() - start)


    console.interact()
