from twocode import utils
import builtins

# a custom execution, written however so it works - nests etc
# an alternative to the eval cascade
# one implemented as a list going on, a pointer travelling the code structure, carrying its memory?
    # what is there to carry - just scopes
    # but! whatever loop it is in could also be implemented to only go 100 steps. or stop.
    # how?
    # at best: write threading, start a thread, receive "eval" signals from the queue
    # and the thread's eval can, base on the node's type, decide to continue executign or not
    # when it hits the bottom level again and knows it's about to exit, it could read the next
    # eval command off the queue (nvm it would do that anyway)

# IndentationError
# FileNotFoundError
# EOFError

# threading:
# context.thread.
# frame, parser, stack

"""
# options:
# string length after each token
# indices of EOL tokens
# analyse "EOL" tokens in the non-transformed tree
# a mapping from original tree to this one - even pos to pos
# + store original string - ParseInfo
    # code.info
"""

# typing fail
# no impl

# move the exc here. maybe.

# sme

def add_exceptions(context):
    def throw(obj):
        exc = context.exc.RuntimeError(obj, [stack.copy() for stack in context.eval_stack])
        raise exc from None
    context.throw = throw

    def stmt_throw(node):
        exc = context.eval(node.tuple, type="expr")
        context.throw(exc)
    def try_chain(node):
        try:
            with context.ScopeContext():
                value = context.eval(node.try_block, type="pass")
                value = context.stmt_value(value)
                return value
        except context.exc.RuntimeError as rt_err:
            for catch_block in node.catch_blocks:
                exc = rt_err.exc
                decl = catch_block.decl
                if decl and decl.type:
                    type = context.eval(decl.type)
                else:
                    type = None
                if type:
                    try:
                        exc = context.convert(exc, type)
                    except context.exc.ConversionError:
                        exc = None
                if exc:
                    with context.ScopeContext():
                        if decl and decl.id:
                            context.declare(decl.id, exc, type)
                        value = context.eval(catch_block.block, type="pass")
                        value = context.stmt_value(value)
                        return value
        finally:
            if node.finally_block:
                with context.ScopeContext():
                    value = context.eval(node.finally_block, type="pass")
                    value = context.stmt_value(value)
                    return value
    context.instructions.update({
        "stmt_throw": stmt_throw,
        "try_chain": try_chain,
        "expr_try": lambda node: context.eval(node.try_chain, type="pass"),
    })
    class RuntimeError(builtins.Exception):
        def __init__(self, exc, eval_stack):
            super().__init__()
            self.exc = exc
            self.eval_stack = eval_stack
        def __str__(self):
            return "\n\n" + context.traceback(self)
    context.exc.RuntimeError = RuntimeError

    Object, Class, Func = [context.obj[name] for name in "Object, Class, Func".split(", ")]

    context.exc_types = utils.Object()
    def gen_class(name):
        cls = context.obj.Class()
        context.exc_types[name] = cls
        return cls
    def attach(cls, name, **kwargs):
        def wrap(func):
            cls.__fields__[name] = Func(native=func, **kwargs)
        return wrap

    Exception = gen_class("Exception")
    def gen_exc(name):
        cls = gen_class(name)
        cls.__base__ = Exception
        return cls
    InternalError = gen_exc("InternalError")
    SyntaxError = gen_exc("SyntaxError")
    NameError = gen_exc("NameError")
    AttributeError = gen_exc("AttributeError")
    ImportError = gen_exc("ImportError")
    TypeError = gen_exc("TypeError")
    ValueError = gen_exc("ValueError")

    # related to some other unfinished eval business as well
    context.eval_stack = [[]]
    old_eval = context.eval
    pass_exc = tuple(context.exc.values())
    def eval(node, type="expr"):
        context.eval_stack[-1].append(node)
        try:
            return old_eval(node, type)
        except context.exc.RuntimeError:
            raise
        except pass_exc:
            raise # workaround, catching with handle_exc sucks tho
        except builtins.Exception as exc:
            context.throw(Object(InternalError, __this__=internal_error_msg(exc)))
        finally:
            context.eval_stack[-1].pop()
    context.eval = eval
    old_call_func = context.call_func
    def call_func(*args, **kwargs):
        # hide this + the exc one in the tb
        context.eval_stack.append([])
        try:
            return old_call_func(*args, **kwargs)
        finally:
            context.eval_stack.pop()
    context.call_func = call_func
    def internal_error_msg(exc):
        lines = []
        tb = exc.__traceback__
        while True:
            filename = tb.tb_frame.f_code.co_filename
            lineno = tb.tb_lineno
            name = tb.tb_frame.f_code.co_name
            if name not in """
                filter eval wrapped <lambda> __matmul__
                call call_func call_method
                check type_check
            """.split():
                lines.append(" " * 2 + 'File "{}", line {}, in {}'.format(filename, lineno, name))
            if tb.tb_next:
                tb = tb.tb_next
            else:
                break
        lines.append("{}: {}".format(type(exc).__qualname__, str(exc)))
        return "\n" + "\n".join(lines)
    context.internal_error_msg = internal_error_msg

    def traceback(exc):
        exc, eval_stack = exc.exc, exc.eval_stack
        r"""
          File "<cell>", line 653
            M.s()
          File "H:\Twocode\code\M.2c", line 20, in s
            f()
          File "H:\Twocode\code\M.2c", line 39, in f
            throw Exception()
        """
        lines = []
        for stack in eval_stack:
            if not stack:
                continue
            # lexical data from node[0]
            # metadata at code / stmt?
            # lexer words iterators
            #    chunks, items
            # file info, line
            for node in reversed(stack):
                type_name = type(node).__name__
                if type_name.startswith("stmt"):
                    break
            line = " " * 4 + str(node).splitlines()[0].lstrip()
            # or from lex data
            # we can tell boundmethod's path, but not static
            # can tell from closure? scope analysis

            # is the internal not missing lines?
            lines.append(line)
        try:
            qualname = context.unwrap(context.operators.qualname.native(exc.__type__))
        except:
            # REASON: if it's a setup error before init_scope
            qualname = "Error"
            for name, exc_type in context.exc_types.items():
                if exc.__type__ is exc_type:
                    qualname = name
                    break
        lines.append("{}: {}".format(qualname, "")) # string operator?
        msg = "\n".join(lines)
        if exc.__type__ is InternalError:
            msg += exc.__this__
        return msg
    context.traceback = traceback
