from twocode import Utils
from twocode.utils.Nodes import switch
import builtins
from twocode.context.Operators import *
from twocode.context.Literals import *

def add_context(context):
    node_types = context.node_types
    access_type = node_types["term_access"]
    call_type = node_types["term_call"]
    arg_type = node_types["call_arg"]
    args_type = node_types["args"]
    call = lambda term, func, args: call_type(access_type(term, func), args_type([arg_type(arg) for arg in args])) # call?

    def add_exceptions():
        class Return(Exception):
            def __init__(self, value=None):
                self.value = value
        class EvalException(Exception):
            pass
        class RuntimeInterrupt(Exception):
            "stop the evaluation of current statement"

        class InvalidIfChainEmpty(Exception):
            "if_chain node has no if_blocks"
        class InvalidIfCondEmpty(Exception):
            "if_block node has empty condition"

        class InvalidPack(Exception):
            "arguments pack in wrong order"
        class InvalidUnpack(Exception):
            "arguments unpack in wrong order"

        context.exc = Utils.Object()
        for name, exception in Utils.redict(locals(), ["context"]).items():
            context.exc[name] = exception
    add_exceptions()

    def add_core():
        def call(func, args):
            # wat?
            func, (args, kwargs) = callable(func, args)
            scope = context.unpack_args(func, (args, kwargs))
            for arg in func.args:
                if not arg.pack:
                    if arg.name in scope:
                        scope[arg.name] = context.wrap_value(scope[arg.name])
                    else:
                        scope[arg.name] = context.eval(arg.default)
                elif arg.pack == "args":
                    scope[arg.name] = context.wrap_value((context.wrap_value(value) for value in scope[arg.name]))
                elif arg.pack == "kwargs":
                    scope[arg.name] = context.wrap_value({name: context.wrap_value(value) for name, value in scope[arg.name].items()})
            return call_func(func, scope)
        def call_func(func, scope):
            try:
                value = None
                if func.native:
                    args, kwargs = context.pack_args(func, scope)
                    args = [context.unwrap_value(arg) for arg in args]
                    kwargs = {key: context.unwrap_value(arg) for key, arg in kwargs.items()}
                    value = func.native(*args, **kwargs)
                    value = context.wrap_value(value)
                    raise context.exc.Return(value)
                else:
                    old_scope = context.swap_stack(func.scope)
                    context.stack.append(scope)
                    context.stack.append(context.new(context.builtins.Scope))
                    context.eval(func.code)
            except context.exc.Return as exc:
                value = exc.value
            finally:
                if not func.native:
                    context.stack.pop()
                    context.stack.pop()
                    context.swap_stack(old_scope)
            return value
        def unpack_args(func, args):
            args, kwargs = args
            args = list(args)
            scope = {}

            for arg in func.args:
                if not arg.pack:
                    if args:
                        scope[arg.name] = args.pop(0)
                    else:
                        if arg.name in kwargs:
                            scope[arg.name] = kwargs[arg.name]
                            del kwargs[arg.name]
                        # else what?
                elif arg.pack == "args":
                    scope[arg.name] = args
                    args = []
                elif arg.pack == "kwargs":
                    scope[arg.name] = kwargs
                    kwargs = {}
            if args or kwargs:
                raise SyntaxError("signature mismatch while unpacking arguments")
            return scope
        def pack_args(func, scope):
            args, kwargs = [], {}
            for arg in func.args:
                if not arg.pack:
                    args.append(scope[arg.name])
                elif arg.pack == "args":
                    args.extend(context.unwrap_value(scope[arg.name]))
                elif arg.pack == "kwargs":
                    kwargs.update(context.unwrap_value(scope[arg.name]))
                del scope[arg.name]
            if scope:
                raise SyntaxError("signature mismatch while packing arguments")

            args = tuple(args)
            return args, kwargs
        def pack_level(pack, name=None):
            if name: return 2
            if not pack: return 0
            if pack == "args": return 1
            if pack == "kwargs": return 2
        def callable(obj, args):
            while True:
                if obj.__type__ is context.builtins.Func:
                    return obj, args
                elif obj.__type__ is context.builtins.Type:
                    obj, args = construct_call(obj, args)
                elif obj.__type__ is context.builtins.BoundMethod:
                    obj, args = bound_method_call(obj, args)
                else:
                    obj, args = obj_call(obj, args)
        def construct_call(type, args):
            Arg = context.obj.Arg
            func = context.obj.Func(native=lambda this, *args, **kwargs: context.construct(this, (args, kwargs)), args=[Arg("this", type=context.builtins.Type), Arg("args", pack="args"), Arg("kwargs", pack="kwargs")])
            # weird
            return func, args
        def bound_method_call(bound_method, args):
            args, kwargs = args
            obj, func = bound_method.obj, bound_method.func
            return func, ((obj, *args), kwargs)
        def obj_call(obj, args):
            func = context.getattr(obj, "__call__")
            return func, args
        def new(type):
            try:
                new = context.getattr(type, "__new__")
                factory = lambda: context.call(new, ((), {}))
            except AttributeError:
                factory = lambda: context.obj.Object(type)
            obj = factory()
            for var, attr in context.inherit_fields(type).items():
                if attr.__type__ is context.builtins.Var:
                    obj[var] = context.eval(attr)
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
                t = t.__base__
            return types
        def inheritable(type, attr):
            if attr.__type__ is context.builtins.Var:
                return True
            if attr.args:
                arg = attr.args[0]
                # if arg.name == "this" and arg.type == type: ## inherit __call__?
                if arg.name == "this": ## inherit __call__?
                    return True
            return False
        def construct(type, args): # uses call, care where we use it
            obj = context.new(type)
            try:
                constructor = context.getattr(obj, "__init__")
            except AttributeError:
                constructor = None
            if constructor:
                context.call(constructor, args)
            return obj
        def unwrap_value(value):
            while isinstance(value, context.obj.Object):
                # if "__this__" in value.__type__.__fields__:
                # and NOT in fields
                try:
                    value = getattr(value, "__this__")
                except AttributeError:
                    break
            return value
        def wrap_value(value):
            t = builtins.type(value)
            if t not in literal_wrap:
                return value
            type = context.builtins[literal_wrap[t]]
            obj = context.obj.Object(type, this=value)
            for var, attr in context.inherit_fields(type).items():
                if attr.__type__ is context.builtins.Var:
                    obj[var] = context.eval(attr.value)
            return obj
        def copy(value):
            assert 0 == 1
            pass #return deepcopy(value)

        def cast(obj, type):
            pass
            # if is return
            # search conversions to
            # search abstract from
            # error
        def defines(obj, name, signature=None):
            try:
                method = context.getattr(obj, name)
            except AttributeError:
                return None
            if method.__type__ is not context.builtins.BoundMethod:
                return None
            # signature
            return method

        for name, instruction in Utils.redict(locals(), ["context"]).items():
            setattr(context, name, instruction)
    add_core()

    def add_assign():
        def term_id(node, value):
            value = context.eval(value)
            context.scope[node.id] = value
            return value


            value = context.eval(value)
            id = node.id
            if id in context.scope:
                return context.scope[id]
            if "this" in context.scope:
                this = context.scope["this"]
                try:
                    return context.getattr(this, id)
                except AttributeError:
                    pass
            raise NameError("name {} is not defined".format(repr(id)))

            # lookup explicit from sources

        def term_access(node, value):
            obj = context.eval(node.term)
            value = context.eval(value)
            return context.setattr(obj, node.id, value)
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
        def type_ref_id(node):
            # print(node)
            return context.scope[node.id]
        def func_def(node):
            func = context.obj.Func()
            if node.id:
                context.declare(node.id, func)
            level = 0
            for arg in node.args:
                arg_pack = context.pack_level(arg.pack, arg.id)
                if arg_pack < level:
                    raise context.exc.InvalidPack()
                else:
                    level = arg_pack

                func_arg = context.obj.Arg()
                func_arg.name = arg.id
                #### print(arg.type)
                func_arg.type = context.eval(arg.type_ref)
                #### print(func_arg.type, builtins.type(func_arg.type))
                # type_id
                if arg.value is not None:
                    func_arg.default = arg.value
                func_arg.pack = arg.pack
                func_arg.macro = arg.macro
                func.args.append(func_arg)
            func.return_type = context.eval(node.return_type) # we cant eval type
            # print("FUNC!")
            # print(node.block)
            func.code = node.block
            func.scope = context.scope.copy()
            return func
        def type_def(node):
            # func.scope = context.scope.copy()
            # not saving for every func is efficient, but actually shouldnt be done
            # what context for the macros?
            # and what about outside, patched funcs/vars?

            # __vars__
            type = context.obj.Type()
            if node.id:
                type.__name__ = context.wrap_value(node.id) # wrap everywhere! a class for it, do it for basic types. Int.__name__
                context.declare(node.id, type)
            if node.base:
                type.__base__ = context.eval(node.base)
            for stmt in node.block.lines:
                type_name = builtins.type(stmt).__name__
                if type_name == "stmt_var": ###
                    decl = stmt.vars[0]
                    var = context.obj.Var()
                    var.type = context.eval(decl.type_ref) if decl.type_ref else context.builtins.Dynamic
                    if stmt.assign_chain:
                        assign = stmt.assign_chain[0]
                        var.value = assign.tuple # fk
                    type.__fields__[decl.id] = var
                    continue
                elif type_name == "stmt_tuple":
                    stmt = stmt.tuple.expr
                    type_name = builtins.type(stmt).__name__
                    if type_name == "expr_func":
                        stmt = stmt.func_def
                        method = context.obj.Func()
                        if not stmt.id:
                            raise SyntaxError("anonymous function in type definition")
                        type.__fields__[stmt.id] = method
                        method.args.append(context.obj.Arg("this", type))
                        for arg in stmt.args:
                            method_arg = context.obj.Arg()
                            method_arg.name = arg.id
                            method_arg.default = arg.value
                            method_arg.pack = arg.pack
                            method.args.append(method_arg)
                        method.return_type = context.eval(stmt.return_type)
                        method.code = stmt.block
                        method.scope = context.scope.copy()
                        continue
                raise SyntaxError("invalid statement in type definition")
            return type
        def in_block(node):
            expr = context.eval(node.expr)
            try:
                value = None
                context.stack.append(expr)
                value = context.eval(node.block)
            finally:
                context.stack.pop()
            return value
            # exec, overloadable, scope wrapper
        def for_loop(node):
            iter = context.eval(node.iter)
            # if retypes to ?
            if context.defines(iter, "has_next") and context.defines(iter, "next"):
                # return types
                iter = iter
            elif context.defines(iter, "iter"):
                iter = call(iter, "iter", [])
            elif context.defines(iter, "__getitem__") and context.hasattr(node, "length"):
                iter = iter ##
            else:
                raise TypeError("{} object is not iterable".format(repr(iter.__type__.__name__)))
            var = node.tuple.expr.term
            value = []
            # type Iter: { var iter = null; func __init__(i): { iter = i }; func has_next(): { return false } }
            # should not be iterable
            while call(iter, "has_next", []).__this__:
                context.scope[var] = call(iter, "next", [])
                value.append(context.eval(node.block))
            return context.wrap_value(value)
        def while_loop(node):
            value = []
            while context.convert(context.eval(node.cond), context.builtins.Bool).__this__:
                value.append(context.eval(node.block))
            return context.wrap_value(value)
        def if_chain(node):
            if not node.if_blocks:
                raise context.exc.InvalidIfChainEmpty()
            for if_block in node.if_blocks:
                if not if_block.cond:
                    raise context.exc.InvalidIfCondEmpty()
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
            if not node.assign_chain:
                context.declare(decl.id, context.eval(assign.tuple)) # null
                return

            # type = context.eval(decl.type) if decl.type else context.builtins.Dynamic
            '''
                    if stmt.assign_chain:
                        assign = stmt.assign_chain[0]
                        value = context.wrap_code(assign.tuple)
                    type.__fields__[decl.id] = Var(value, type)
            '''

            assign = node.assign_chain[0]
            # context.scope[decl.id] = Value(context.eval(assign.tuple))
            context.declare(decl.id, context.eval(assign.tuple))
        def stmt_return(node):
            raise context.exc.Return(context.eval(node.tuple))
        def stmt_import(node):
            for path in node.imp.imports:
                module = context.imp(".".join(path.path))
                context.declare(path.path[-1], module)
                # rename, from etc
        def term_id(node):
            # scope.id
            # sources.id
            # scope.this.id



            id = node.id
            if id in context.scope:
                return context.scope[id]
            if "this" in context.scope:
                this = context.scope["this"]
                try:
                    return context.getattr(this, id)
                except AttributeError:
                    pass
            raise NameError("name {} is not defined".format(repr(id)))
        # t vs e order?
        def term_access(node):
            obj = context.eval(node.term)
            return context.getattr(obj, node.id) # !!!
        def term_index(node):
            ast = call(node.term, "__getitem__", [node.tuple])
            return context.eval(ast)
        def term_call(node):
            args, kwargs = [], {}
            level = 0
            for arg in node.args.args:
                arg_pack = context.pack_level(arg.pack, arg.id)
                if arg_pack < level:
                    raise context.exc.InvalidUnpack()
                else:
                    level = arg_pack

                code = arg.value
                if arg.id:
                    kwargs[arg.id] = code
                if not arg.pack:
                    args.append(code)
                if arg.pack == "args":
                    args.extend(code) #
                if arg.pack == "kwargs":
                    kwargs.update(code) # wat

            func = context.eval(node.term)
            func, args = context.callable(func, (args, kwargs))
            scope = context.unpack_args(func, args)
            eval = lambda value: context.eval(value) if not arg.macro else context.wrap_code(value)
            for arg in func.args:
                if not arg.pack:
                    if arg.name in scope:
                        scope[arg.name] = eval(scope[arg.name])
                    else:
                        scope[arg.name] = context.eval(arg.default)
                elif arg.pack == "args":
                    scope[arg.name] = context.wrap_value((eval(value) for value in scope[arg.name]))
                elif arg.pack == "kwargs":
                    scope[arg.name] = context.wrap_value({name: eval(value) for name, value in scope[arg.name].items()})
            return context.call_func(func, scope)
        def term_list(node):
            type = context.builtins.List
            obj = context.new(type)
            items = context.eval(node.tuple)
            obj.__this__ = list(items) if builtins.type(items) is builtins.tuple else [items]
            print(builtins.type(obj.__this__), len(obj.__this__))
            print("t", builtins.type(obj.__type__))
            return obj
        def term_map(node):
            type = context.builtins.Map
            obj = context.new(type)
            obj.__this__ = {}
            for item in node.map.item_list:
                key = context.eval(item.key)
                key = context.unwrap_value(key) # unwrap? !!!
                value = context.eval(item.value)
                obj.__this__[key] = value
            return obj
        def literal(node):
            l_type = node.lit_type
            value = literal_eval[l_type](node.value)
            return context.wrap_value(value)
            # REASON: constructors send a string literal to native(), causing recursion
            # new looks up __new__ with getattr, which uses call for its args, which wraps values and creates literals
        def expr_term(node):
            obj = context.eval(node.term)
            type = obj.__type__
            try:
                op = context.getattr(type, "__expr__")
            except AttributeError:
                op = None
            if op:
                obj = context.call(op, ((obj,), {}))
            return obj
        def expr_math(node):
            a = context.eval(node.expr1)
            b = context.eval(node.expr2)
            type = a.__type__
            # print("want", node.op)
            op = context.getattr(type, op_math[node.op]) # !!!
            # print(builtins.type(a), builtins.type(type), builtins.type(b))
            return context.call(op, ((a, b), {}))
        def expr_compare(node):
            a = context.eval(node.expr1)
            b = context.eval(node.expr2)
            type = a.__type__
            op = context.getattr(type, op_compare[node.op]) # !!!
            return context.call(op, ((a, b), {}))
        def expr_affix(node):
            obj = context.eval(node.term)
            op = None
            if node.op == "++":
                op = increment
            elif node.op == "--":
                op = decrement
            if node.affix == "prefix":
                op(obj)
            result = context.wrap_value(obj.__this__)
            if node.affix == "postfix":
                op(obj)
            return result
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
            obj = call(a, "contains", [b]) # all instances of call,... getattr... how do i store the keys? !!!
            obj = context.convert(obj, context.builtins.Bool)
            return obj
        def expr_decorator(node): # rename? map a -> b, map_call
            # function retains name
            decorator = context.eval(node.term)
            if not decorator.args[0].macro:
                obj = context.eval(node.expr)
            else:
                obj = context.wrap_code(node.expr)
            return context.call(decorator, ((obj,), {}))
        def expr_macro(node):
            return context.wrap_code(node.code)
        tuple = lambda node: builtins.tuple(context.eval(expr) for expr in node.expr_list)
        tuple_expr = lambda node: context.eval(node.expr)
        expr_unary = lambda node: context.eval(call(node.term, op_unary[node.op], []))
        expr_block = lambda node: context.eval(node.block)
        expr_if = lambda node: context.eval(node.if_chain)
        expr_try = lambda node: context.eval(node.try_chain)
        expr_for = lambda node: context.eval(node.for_loop)
        expr_while = lambda node: context.eval(node.while_loop)
        expr_in_block = lambda node: context.eval(node.in_block)
        expr_func = lambda node: context.eval(node.func_def)
        expr_type = lambda node: context.eval(node.type_def)
        term_literal = lambda node: context.eval(node.literal)
        term_tuple = lambda node: context.eval(node.tuple)

        instructions = dict(locals())
        context.eval = switch(instructions, key=lambda node: builtins.type(node).__name__)
    add_eval()

    log_default = context.__getattribute__
    def log_f(name, attr, *args, **kwargs):
        args_str = []
        def to_str(obj):
            s = repr(obj)
            if len(s) > 500:
                return "?-Type"
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
