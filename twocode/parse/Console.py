import sys
from twocode import Utils
import traceback
from codeop import CommandCompiler
import twocode.utils.Code

class Console:
    def __init__(self, scope={}, shell=True):
        self.scope = scope
        self.shell = shell

        compiler = CommandCompiler()
        self.compile = lambda code: compiler(code, "<console>", "single")
        self.buffer = []

        self.streams = Utils.streams_object(None)
        self.sys_streams = Utils.wrap_streams(Utils.streams_object(sys), Utils.FlushStream)

        self.context = lambda: Utils.cond_context(lambda: not self.shell,
            self.streams,
            self.sys_streams,
        )
        self.silent = Utils.Streams(stdout=Utils.NullStream(), stderr=Utils.NullStream())
    def run(self, code):
        ast = self.compile(code)
        if ast is None:
            return True
        self.exec(ast)
        return False
    def parse(self, code, silent=False):
        with self.context():
            contexts = Utils.contexts()
            if silent:
                contexts.contexts += [self.silent]
            with contexts:
                try:
                    self.exec(code)
                except EOFError:
                    pass
                except SystemExit:
                    pass
    def interact(self):
        more = False
        prompt_msg = lambda: ">>> " if not more else "... "
        with self.context():
            self.buffer = []
            while True:
                try:
                    if self.shell:
                        print(prompt_msg(), file=sys.stderr, flush=True, end="")
                    line = sys.stdin.readline()
                    if line:
                        line = line.rstrip("\r\n")
                    else:
                        raise EOFError()
                    self.buffer.append(line)
                    code = "\n".join(self.buffer)
                    more = self.run(code)
                    if not more:
                        self.buffer = []
                except KeyboardInterrupt:
                    print("\nKeyboardInterrupt\n", file=sys.stderr, flush=True, end="")
                    more = False
                    self.buffer = []
                except EOFError:
                    return
                except SystemExit:
                    return
                except:
                    more = False
                    self.buffer = []
                    exc_class, exc, tb = twocode.utils.Code.skip_exc_info(depth=3)
                    msg = traceback.format_exception(exc_class, exc, tb)
                    print("".join(msg), file=sys.stderr, flush=True, end="")
    def eval(self, code):
        with self.context():
            obj = eval(code, self.scope)
        return obj
    def exec(self, code):
        with self.context():
            exec(code, self.scope)

if __name__ == "__main__":
    Utils.streams_encoding(sys, "utf-8")()
    console = Console()
    console.interact()