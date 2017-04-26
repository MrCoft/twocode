from twocode.context.Objects import *
from twocode import Utils
from twocode.utils.Nodes import switch
import builtins
from twocode.context.Operators import *
from twocode.context.Literals import *
from copy import deepcopy

def add_context(context):
    node_types = context.node_types
    access_type = node_types["term_access"]
    call_type = node_types["term_call"]
    arg_type = node_types["call_arg"]
    args_type = node_types["args"]
    call = lambda term, func, args: call_type(access_type(term, func), args_type([arg_type(arg) for arg in args]))
    make_args = lambda *args, **kwargs: (args, kwargs) ###
    parens_type = node_types["term_tuple"]

    context.scope = Scope()
    context.stack = context.scope.stack

    def add_core():
        def swap_stack(scope):
            if scope is None: scope = Scope() # weird. also builtins into normal one?
            old_scope = context.scope
            context.scope = scope
            context.stack = scope.stack
            return old_scope
        def declare(name, obj):
            context.stack[-1][name] = obj
        # # if type is None?
        # parse
        def getattr(obj, name):
            type = obj.__type__
            if name in context.metafields(type):
                return obj[name]
            if "__getattr__" in type.__fields__:
                try:
                    return context.call(type.__fields__["__getattr__"], ([obj, name], {}))
                except AttributeError:
                    pass
            fields = context.inherit_fields(type)
            if name in fields:
                attr = fields[name]
                if attr.__type__ is not Func.__type__:
                    return obj[name]
                else:
                    return obj.__bound__[name]
            raise AttributeError("{} object has no attribute {}".format(repr(type.__name__), repr(name)))
        def setattr(obj, name, value):
            type = obj.__type__
            if name in context.metafields(type):
                obj[name] = value
                return obj[name]
            if "__setattr__" in type.__fields__:
                try:
                    return context.call(type.__fields__["__setattr__"], ([obj, name, value], {}))
                except AttributeError:
                    pass
            fields = context.inherit_fields(type)
            if name in fields:
                attr = fields[name]
                if attr.__type__ is not Func.__type__:
                    obj[name] = value
                    return obj[name]
            raise AttributeError("{} object has no attribute {}".format(repr(type.__name__), repr(name)))
        def call(obj, args):
            if type(obj) is Func:
                return func_call(obj, args)
            elif type(obj) is Class:
                return construct(obj, args)
            elif type(obj) is BoundMethod:
                return bound_method_call(obj, args)
            else:
                return obj_call(obj, args)
        def pass_args(func, args):
            args, kwargs = args
            scope = {}
            for arg in func.args:
                if not arg.pack:
                    if args:
                        scope[arg.name] = args.pop(0)
                    else:
                        if arg.name in kwargs:
                            scope[arg.name] = kwargs[arg.name]
                            del kwargs[arg.name]
                        else:
                            scope[arg.name] = context.eval(context.unwrap_code(arg.default))
                elif arg.pack == "args":
                    scope[arg.name] = args
                    args = []
                elif arg.pack == "kwargs":
                    scope[arg.name] = kwargs
                    kwargs = {}
            return scope
        def func_call(func, args):
            args, kwargs = args
            old_scope = context.swap_stack(func.scope)
            try:
                value = None
                if func.native:
                    args = [context.unwrap_value(arg) for arg in args]
                    kwargs = {key: context.unwrap_value(arg) for key, arg in kwargs.items()}
                    value = func.native(*args, **kwargs)
                    value = context.wrap_value(value)
                    raise Return(value)
                else:
                    context.stack.append(context.pass_args(func, (args, kwargs)))
                    context.stack.append({})
                    context.eval(context.unwrap_code(func.code))
            except Return as exc:
                value = exc.value
            finally:
                if not func.native:
                    context.stack.pop()
                    context.stack.pop()
                context.swap_stack(old_scope)
            return value
        def obj_call(obj, args):
            func = context.getattr(obj, "__call__")
            return context.call(func, args)
        def bound_method_call(bound_method, args):
            args, kwargs = args
            obj, func = bound_method.obj, bound_method.func
            return context.call(func, ([obj] + args, kwargs))
        def new(cls): # __new__
            obj = Object(cls)
            obj.__type__ = cls
            for var, attr in context.inherit_fields(cls).items():
                if attr.__type__ is not Func.__type__:
                    obj[var] = context.copy(attr) # eval
                else:
                    obj.__bound__[var] = BoundMethod(obj, attr)
            return obj
        def inherit_fields(type):
            fields = {}
            for t in context.inherit_chain(type):
                for var, attr in t.__fields__.items():
                    if context.inheritable(t, attr):
                        fields[var] = attr
            return fields
        def inherit_chain(t):
            types = []
            while t:
                types.insert(0, t)
                t = t.__parent__
            return types
        def inheritable(type, attr):
            if attr.__type__ is not Func.__type__:
                return True
            else:
                if len(attr.args):
                    arg = attr.args[0]
                    if arg.name == "this" and arg.type == type:
                        return True
            return False
        def construct(cls, args):
            obj = context.new(cls)
            try:
                constructor = context.getattr(obj, "__init__")
            except AttributeError:
                constructor = None
            if constructor:
                context.call(constructor, args)
            return obj
        def metafields(t):
            fields = set()
            fields.update("__type__ __bound__".split()) # __this__
            return fields
        def unwrap_value(value):
            while isinstance(value, Object):
                # if "__this__" in value.__type__.__fields__:
                if "__this__" in value.__dict__:
                    value = value.__dict__["__this__"]
                else:
                    break
            return value
        def wrap_value(value):
            t = type(value)
            if t not in literal_wrap:
                return value
            obj = context.new(context.builtins[literal_wrap[t]])
            obj.__this__ = value
            return obj
        def copy(value):
            return deepcopy(value)

        def cast(obj, type):
            pass
            # if is return
            # search conversions to
            # search abstract from
            # error

        for name, instruction in Utils.redict(locals(), ["context"]).items():
            context.__dict__[name] = instruction
    add_core()

    def add_assign():
        def term_ID(node, value):
            value = context.eval(value)
            context.scope[node.ID] = value
            return value
        def term_access(node, value):
            obj = context.eval(node.term)
            value = context.eval(value)
            return context.setattr(obj, node.ID, value)
        def term_index(node, value):
            ast = call(node.term, "__setitem__", [node.tuple, value])
            return context.eval(ast)

        instructions = locals()
        context.assign = lambda node, value: instructions[type(node).__name__](node, value)
    add_assign()

    def add_eval():
        def code(node):
            value = None
            for stmt in node.lines:
                value = context.eval(stmt)
            return value
        def func(node):
            func = Func() # __bound__
            if node.ID:
                context.declare(node.ID, func)
            for arg in node.args:
                func_arg = Arg() # **
                func_arg.name = arg.ID
                func_arg.default = context.wrap_code(arg.value)
                func_arg.pack = arg.pack
                func.args.append(func_arg)
            func.return_type = context.eval(node.return_type) # we cant eval type
            func.code = context.wrap_code(node.block)
            func.scope = context.scope.copy()
            return func
        def _class(node):
            cls = Class()
            if node.ID:
                cls.__name__ = node.ID
                context.declare(node.ID, cls)
            scope = {} #########
            # A.__fields__
            context.stack.append(scope)
            context.declare("__call__", Func(native=lambda: context.new(cls))) # thats not how it works?
            try:
                context.eval(node.block)
            finally:
                context.stack.pop()
            cls.__fields__.update(scope)
            return cls
        def for_loop(node):
            iter = context.eval(node.iter)
            if "has_next" in iter.__bound__ and "next" in iter.__bound__:
                iter = iter
            elif "iter" in iter.__bound__:
                iter = call(iter, "iter", [])
            elif "__getitem__" in iter.__bound__ and context.hasattr(node, "length"):
                iter = iter ##
            else:
                raise TypeError("{} object is not iterable".format(repr(iter.__type__.__name__)))
            var = node.tuple.expr.term
            value = []
            while call(iter, "has_next", []).__this__:
                context.scope[var] = call(iter, "next", [])
                value.append(context.eval(node.block))
            return value
        def while_loop(node):
            value = []
            while context.convert(context.eval(node.cond), context.builtins.Bool).__this__:
                value.append(context.eval(node.block))
            return value
        def if_chain(node):
            for if_block in node.if_blocks:
                value = context.eval(if_block.cond)
                if context.convert(value, context.builtins.Bool).__this__: #
                    return context.eval(if_block.block)
            if node.else_block:
                return context.eval(node.else_block)
        def stmt_tuple(node):
            return context.eval(node.tuple)
        def stmt_assign(node):
            lvalue = node.tuple.expr.term
            assign = node.assign_chain[0]
            op = assign.op
            rvalue = assign.tuple.expr
            return context.assign(lvalue, rvalue) # support operators
        def stmt_var(node):
            decl = node.vars[0]
            assign = node.assign_chain[0]
            # context.scope[decl.ID] = Value(context.eval(assign.tuple))
            context.declare(decl.ID, context.eval(assign.tuple))
        def stmt_return(node):
            raise Return(context.eval(node.tuple))
        def args(node):
            args, kwargs = [], {}
            for arg in node.args:
                value = context.eval(arg.value)
                if arg.ID:
                    kwargs[arg.ID] = value
                if not arg.pack:
                    args.append(value)
                if arg.pack == "args":
                    args.extend(value)
                if arg.pack == "kwargs":
                    kwargs.update(value)
            return args, kwargs
        def term_ID(node):
            return context.scope[node.ID]
        def term_access(node):
            obj = context.eval(node.term)
            return context.getattr(obj, node.ID)
        def term_index(node):
            ast = call(node.term, "__getitem__", [node.tuple])
            return context.eval(ast)
        def term_call(node):
            func = context.eval(node.term)
            args, kwargs = context.eval(node.args)
            return context.call(func, (args, kwargs))
        def term_array(node):
            type = context.builtins.List
            obj = context.new(type)
            items = context.eval(node.tuple)
            obj.__this__ = list(items) if builtins.type(items) is builtins.tuple else [items]
            return obj
        def literal(node):
            l_type = node.type
            type_name = literal_type[l_type]
            type = context.builtins[type_name]
            value = literal_eval[l_type](node.value)
            obj = context.new(type) # pass
            # REASON: constructors send a string literal to native(), causing recursion
            obj.__this__ = value
            return obj

        def expr_math(node):
            a = context.eval(node.expr1)
            b = context.eval(node.expr2)
            type = a.__type__
            op = context.getattr(type, op_math[node.op])
            return context.call(op, ([a, b], {}))
        def expr_compare(node):
            a = context.eval(node.expr1)
            b = context.eval(node.expr2)
            type = a.__type__
            op = context.getattr(type, op_compare[node.op])
            return context.call(op, ([a, b], {}))
        def expr_bool(node):
            a = context.convert(context.eval(node.expr1), context.builtins.Bool).__this__
            b = context.convert(context.eval(node.expr2), context.builtins.Bool).__this__
            obj = None
            if node.op == "and":
                obj = a and b
            if node.op == "or":
                obj = a or b
            return context.wrap_value(obj)
        def expr_not(node):
            obj = context.convert(context.eval(node.expr), context.builtins.Bool).__this__
            obj = not obj
            return context.wrap_value(obj)
        def expr_in(node):
            a = context.eval(node.expr1)
            b = context.eval(node.expr2)
            obj = call(a, "contains", [b])
            obj = context.convert(obj, context.builtins.Bool)
            return obj
        tuple = lambda node: builtins.tuple(context.eval(expr) for expr in node.expr_list)
        tuple_expr = lambda node: context.eval(node.expr)
        expr_term = lambda node: context.eval(node.term)
        #expr_unary = lambda node: context.eval(call(node.term, op_unary[node.op], []))
        expr_unary = lambda node: context.eval(call(node.term, op_unary[node.op], []))
        # expr_affix
        expr_block = lambda node: context.eval(node.block)
        expr_if = lambda node: context.eval(node.if_chain)
        expr_try = lambda node: context.eval(node.try_chain)
        expr_for = lambda node: context.eval(node.for_loop)
        expr_while = lambda node: context.eval(node.while_loop)
        expr_func = lambda node: context.eval(node.func)
        expr_class = lambda node: context.eval(node.__dict__["class"])
        term_literal = lambda node: context.eval(node.literal)
        term_tuple = lambda node: context.eval(node.tuple)

        instructions = dict(locals())
        instructions["class"] = _class
        del instructions["_class"]
        context.eval = switch(instructions, key=lambda node: type(node).__name__)

    add_eval()

    log_default = context.__getattribute__
    def log_f(name, attr, *args, **kwargs):
        args_str = []
        def to_str(obj):
            s = repr(obj)
            if len(s) > 500:
                if type(obj) is Class:
                    return obj.__name__
                if hasattr(obj, "__type__"):
                    return obj.__type__.__name__
                return type(obj).__name__
            return s.strip()
        for arg in args:
            args_str.append(to_str(arg))
        for key, arg in kwargs.items():
            args_str.append("{}={}".format(key, to_str(arg)))
        msg = "{}({})".format(name, ", ".join(args_str))
        print(msg)
        return attr(*args, **kwargs)
    def log_get(self, name):
        attr = log_default(name)
        if callable(attr):
            return lambda *args, **kwargs: log_f(name, attr, *args, **kwargs)
        print(name)
        return attr
    class log_mode:
        def __enter__(self):
            setattr(
                type(context),
                "__getattribute__",
                log_get
            )
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            delattr(type(context), "__getattribute__")
    context.log_mode = log_mode
# lambda args kwargs: A.x(a, args kwargs)
# make stmts not return anything pls - not an assignment chain

'''
# to eval - unwrap code
# default for ast?
    # how is it made anyway?
    # kwarg check

# tuple type
'''

# @staticmethod

# += -> test +=, then to = +
# operators attempts

if __name__ == "__main__":
    from utils.UnitTest import unit_test ### port to git
    import Context
    unit_test(Context)