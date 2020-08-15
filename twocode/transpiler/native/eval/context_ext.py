
class EvalContext:
    def eval(self, code):
        exec(code, self.scope)
