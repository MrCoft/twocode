from twocode import Utils
from twocode.utils.Nodes import switch
import builtins
from twocode.context.Operators import op_assign, op_compare, op_math, op_unary, increment, decrement
from twocode.utils.Code import inline_exc, InlineException

def add_context(context):

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
            """
                func can be any callable
                args don't have to be wrapped
                macro has been applied

                used by many context parts
                not used by term_call because of macro arguments

                NOTE:
                we use (args, kwargs) because *args, **kwargs aren't universal
                an (obj, *args, **kwargs) signature can't pass an "obj" keyword
            """
            func, (args, kwargs) = context.callable(func, args)
            scope = context.unpack_args(func, (args, kwargs))
            # error
            # if not in scope, but in args, and not pack

            # nam value   key arg
            return context.call_func(func, scope)
        def call_method(obj, method, *args):
            """
                an utility function
                it lacks **kwargs for safety
            """
            return context.call(context.impl(obj.__type__, method), ([obj, *args], {}))
        def call_func(func, scope):
            """
                expects a scope
                args, kwargs packed
                wraps args and sets defaults as neither call nor term_call need to do it
            """
            scope = {name: context.wrap(arg) for name, arg in scope.items()} # down
            # wrong args error where? test for exact msg
            # ex f(a, b) f(1) - missing positional argument -   f(a, pos=b) when there's no pos
            # missing keyword argument when there's no default
            for arg in func.args:
                if arg.default_:
                    if arg.name not in scope:
                        scope[arg.name] = context.eval(arg.default_)
            try:
                return_value = None
                if func.native:
                    # NOTE:
                    # does not swap the frame for efficiency
                    # this does not limit functionality
                    args, kwargs = context.pack_args(func, scope)
                    return_value = func.native(*args, **kwargs)
                else:
                    frame = func.frame.copy() if func.frame else [context.scope.get_env()]
                    bound = "this" in scope and context.bound(func, scope["this"].__type__)
                    # weird. if the type was a mismatch we would not be calling it.
                    if bound:
                        frame.append(context.obj.Object(context.scope_types.ObjectScope, object=scope["this"]))
                    scope = {key: context.obj.Var(value) for key, value in scope.items()}
                    frame.append(context.obj.Object(context.scope_types.Scope, __this__=scope))
                    frame.append(context.obj.Object(context.scope_types.Scope, __this__={}))
                    # cheated, fast creation construction?
                    # test if it would be even possible with construct
                    with context.FrameContext(frame):
                        context.eval(func.code)
            except context.exc.Return as exc:
                return_value = exc.value
            if return_value is None:
                return_value = context.wrap(None)
            return return_value
        def unpack_args(func, args):
            """
                uses the func's args to sort (args, kwargs) into a scope

                is transparent to moved values
                because term_call needs named slots to macro

                used by call and term_call
            """
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
                        # else what?
                elif arg.pack == "args":
                    scope[arg.name] = args
                    args = []
                elif arg.pack == "kwargs":
                    scope[arg.name] = kwargs
                    kwargs = {}
            if args or kwargs:
                # print(args, kwargs)
                raise SyntaxError("signature mismatch while unpacking arguments")
                # obj1 obj2 len=obj3
                # unused arguments
                raise SyntaxError("unused arguments: {}".format(" ".join(kwargs.keys())))
            return scope
        def pack_args(func, scope):
            """
                turns scope into (args, kwargs)

                used to call native functions
            """
            args, kwargs = [], {}
            level = 0
            for arg in func.args:
                if not arg.pack: # ERRORS ON NAMES?
                    if level == 0:
                        args.append(scope[arg.name])
                    else:
                        kwargs[arg.name] = scope[arg.name]
                elif arg.pack == "args":
                    args.extend(context.unwrap(scope[arg.name]))
                    level = 1
                elif arg.pack == "kwargs":
                    kwargs.update(context.unwrap(scope[arg.name]))
                    level = 2
                del scope[arg.name]
            if scope:
                # print("ERR", scope.keys())
                raise SyntaxError("signature mismatch while packing arguments")

            return args, kwargs
        def pack_level(pack, name=None):
            if name: return 2
            if not pack: return 0
            if pack == "args": return 1
            if pack == "kwargs": return 2
        @inline_exc(TypeError)
        def callable(obj, args):
            while True:
                if obj.__type__ is context.objects.Func:
                    return obj, args
                elif obj.__type__ is context.objects.Class:
                    obj, args = construct_call(obj, args)
                elif obj.__type__ is context.objects.BoundMethod:
                    obj, args = bound_method_call(obj, args)
                elif context.impl(obj.__type__, "__call__"):
                    obj, args = obj_call(obj, args)
                else:
                    raise InlineException("{} object is not callable".format(context.unwrap(context.operators.qualname.native(obj.__type__))))
        def construct_call(type, args):
            Arg = context.obj.Arg
            # print("constr", type, args)
            func = context.obj.Func(native=lambda *args, **kwargs: context.construct(type, (list(args), kwargs)), args=[Arg("args", pack="args"), Arg("kwargs", pack="kwargs")])
            # weird
            return func, args
        def bound_method_call(bound_method, args):
            args, kwargs = args
            obj, func = bound_method.obj, bound_method.func_
            return func, ([obj, *args], kwargs)
        def obj_call(obj, args):
            args, kwargs = args
            func = context.impl(obj.__type__, "__call__")
            if not func:
                raise TypeError("{} object is not callable".format(context.unwrap(context.operators.qualname.native(obj.__type__))))
            return func, ([obj, *args], kwargs)
        def new(type):
            new = context.impl(type, "__new__")
            # new SHOULD set vars to null, its weird without it - fill the slots even WITHOUT their default values?
            # nah, do defaults
            if new:
                return context.call(new, ([], {}))
            return context.obj.Object(type)
        def inherit_chain(type):
            types = []
            while type:
                types.insert(0, type)
                type = type.__base__
            return types
        def inherit_fields(type):
            fields = {}
            for t in context.inherit_chain(type):
                for var, attr in t.__fields__.items():
                    # if context.inherits(t, attr):
                    # waiting to solve math.add(a, b)
                    fields[var] = attr
            return fields
        def inherits(type, attr):
            if attr.__type__ is context.objects.Var:
                return True
            try:
                func, args = context.callable(attr, ([], {}), inline_exc=True)
            except InlineException:
                raise Exception("field not var or callable: {}".format(repr(attr)))
            if context.bound(func, type):
                return True
            return False
        def bound(func, type):
            return func.args and func.args[0].name == "this" # and func.args[0].type in context.inherit_chain(type)
            # waiting for types
        def construct(type, args):
            args, kwargs = args
            obj = context.new(type)
            for var, attr in context.inherit_fields(type).items():
                if attr.__type__ is context.objects.Var: #
                    if attr.value:
                        obj[var] = context.eval(attr.value)
                    else:
                        # turn off, types dont work yet
                        impl = None
                        # impl = context.impl(attr.type.__type__, "__default__")
                        if impl:
                            obj[var] = context.call(impl, ([], {}))
                        else:
                            obj[var] = context.wrap(None) #
            constructor = context.impl(type, "__init__")
            if constructor:
                context.call(constructor, ([obj, *args], kwargs))
            return obj
        def impl(type, name, signature=None):
            """
                the way to check if a type implements a method

                when a native type wants to access its method without the option of it being overridden,
                use type.__fields__[name] or type.__base__.__fields__[name] instead

                GETATTR PROBLEM:
                the context used to ask for implementation through getattr
                classess offer their functions through __getattr__, but inherit their own methods as well
                a class which defined a repr stopped printing
                __getattr__ makes sense for scope access, we can still edit code for interfaces






                MATH PROBLEM:


                accessing add(a, b) is weird
                you cannot do impl because the first argument isn't "this"
                you cannot even delegate from that to the type because it isn't an inherited field for the same reason
                and getattr-ing it from the class risks accessing some property of the class instead

                still mention, though, that all the class history have their own fields


                # should __getattr__ be inherited?
            """
            fields = context.inherit_fields(type)
            if not name in fields:
                return None
            func = fields[name]
            try:
                context.callable(func, ([], {}), inline_exc=True)
            except InlineException:
                return None
            return func
            # signature
            # interface? for vars?

            # in python, which uses __new__ and alike the most, ALL funcs are inherited. you do def x() with no self and C(B) has it
            # you cascade until you find a __new__, same for add, which is static. everything is really
            # but obj.f must have f have this

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
                    return context.getattr(this, id, inline_exc=True)
                except InlineException:
                    pass
            raise NameError("name {} is not defined".format(repr(id)))

            # lookup explicit from sources

        def term_attr(node, value):
            obj = context.eval(node.term)
            value = context.eval(value)
            return context.setattr(obj, node.id, value)
        def term_key(node, value):
            obj = context.eval(node.term)
            key = context.eval(node.tuple)
            value = context.eval(value)
            context.operators.setitem.native(obj, key, value)

            # why eval value? :|
            # return value
        instructions = locals()
        context.assign = lambda node, value: instructions[builtins.type(node).__name__](node, value)
    add_assign()

    def add_eval():
        def code(node):
            for stmt in node.lines[:-1]:
                context.eval(stmt)
            if node.lines:
                value = context.eval(node.lines[-1])
            else:
                value = context.obj.Object(context.basic_types.Null)
            return value
        def type_id(node):
            return context.scope[node.id]
        def type_params(node):
            for param in node.params.args: # too much
                # call_arg. func_def does that manually
                type = context.eval(param)
            return context.scope[node.id]
        def type_func(node):
            for type_node in node.arg_types:
                type = context.eval(type_node)
            for type_node in node.return_types:
                type = context.eval(type_node)
            # return what
        def type_tuple(node):
            for type_node in node.types:
                type = context.eval(type_node)
            # return what
        def func_def(node):
            func = context.obj.Func()
            if node.id:
                context.declare(node.id, func)
                # don't if it fails?
            level = 0
            for arg in node.args:
                arg_pack = context.pack_level(arg.pack, arg.id)
                if arg_pack < level:
                    raise context.exc.InvalidPack()
                else:
                    level = arg_pack

                func_arg = context.obj.Arg()
                func_arg.name = arg.id
                func_arg.type = context.eval(arg.type)
                func_arg.default_ = arg.default
                func_arg.pack = arg.pack
                func_arg.macro_ = arg.macro
                func.args.append(func_arg)
            func.return_type = context.eval(node.return_type)
            func.code = node.block
            func.frame = context.scope.frame_copy()
            if not node.id:
                return func
        def class_def(node):
            # func.scope = context.scope.copy()
            # not saving for every func is efficient, but actually shouldnt be done
            # what context for the macros?
            # and what about outside, patched funcs/vars?

            # __vars__
            cls = context.obj.Class() # cls?
            if node.id:
                cls.__name__ = context.wrap(node.id) # wrap everywhere! a class for it, do it for basic types. Int.__name__
                context.declare(node.id, cls)
                # don't?
            if node.base:
                cls.__base__ = context.eval(node.base)
            for stmt in node.block.lines:
                type_name = builtins.type(stmt).__name__
                if type_name == "stmt_var": ###
                    decl = stmt.vars[0]
                    var = context.obj.Var()
                    var.type = context.eval(decl.type.type) if decl.type else None # eval None is None?
                    if stmt.assign_chain:
                        assign = stmt.assign_chain[0]
                        var.value = assign.tuple # fk
                    cls.__fields__[decl.id] = var
                    continue
                elif type_name == "stmt_tuple":
                    stmt = stmt.tuple.expr
                    type_name = builtins.type(stmt).__name__
                    if type_name == "expr_func":
                        stmt = stmt.func_def
                        method = context.obj.Func()
                        if not stmt.id:
                            raise SyntaxError("anonymous function in type definition")
                        cls.__fields__[stmt.id] = method
                        method.args.append(context.obj.Arg("this", cls))
                        for arg in stmt.args:
                            method_arg = context.obj.Arg()
                            method_arg.name = arg.id
                            method_arg.default_ = arg.default
                            method_arg.pack = arg.pack
                            method.args.append(method_arg)
                        method.return_type = context.eval(stmt.return_type)
                        method.code = stmt.block
                        method.frame = context.scope.frame_copy()
                        continue
                raise SyntaxError("invalid statement in class definition")
            if not node.id:
                return cls
        def in_block(node):
            obj = context.eval(node.expr)
            impl = context.impl(obj.__type__, "__code__")
            # what if wrong args? error?
            if impl and impl.args and impl.args[1].macro_:
                return context.call(impl, ([obj, context.wrap_code(node.block)], {}))

            return context.builtins.eval.native(node.block, obj, None)
            # weird, because wrap disallows scope=obj, but would i have to call it weirdly?
            # Scope.Var is really not how it works. Ref?
            # Attr for Class?



            # push extra layer?
            # in gpu:
            # would mean any access to a real name prioritizes this
            # yet var would just keep on doing stuff

            #  SCOPE PUSH, BLOCK EVAL
            # in entry    -  executes it in a swapped scope

            try:
                value = None
                context.stack.append(obj) # works? no. getattr!
                value = context.eval(node.block)
            finally:
                context.stack.pop()



            return value
        def for_loop(node):
            iter = context.eval(node.iter)
            while True:
                has_next = context.impl(iter.__type__, "has_next")
                next = context.impl(iter.__type__, "next")
                if has_next and next:
                    break
                while True:
                    impl = context.impl(iter.__type__, "iter")
                    if impl:
                        iter = context.call(impl, ([iter], {}))
                        break
                    impl = context.impl(iter.__type__, "__getitem__")
                    if impl and context.hasattr(iter, "length"):
                        iter = iter # iter over
                        break
                    raise TypeError("{} object is not iterable".format(repr(context.unwrap(context.operators.qualname.native(iter.__type__))))) #
                has_next = context.impl(iter.__type__, "has_next")
                next = context.impl(iter.__type__, "next")

            has_next = context.obj.BoundMethod(iter, has_next)
            next = context.obj.BoundMethod(iter, next)

            # iter operator

            # FIX
            context.stack.append(context.construct(context.scope_types.Scope, ([], {}))) # vars if any
            # print(context.stack[-1].keys())
            # avoid, like in all of context
            var = node.var.expr.term.id
            # print("VAR", var, builtins.type(var))
            # >>> printing null

            # item
            context.declare(var, None) # allow to have type only i guess? default to Dynamic none?
            try:
                list_compr = []
                while True:
                    cond = context.call(has_next, ([], {}))
                    cond = context.unwrap(cond)
                    if not cond:
                        break

                    context.scope[var] = context.call(next, ([], {}))
                    value = context.eval(node.block)
                    list_compr.append(value)
                # gen_compr
            # except break, continue
            finally:
                context.stack.pop()
            list_compr = context.wrap(list_compr)
            return list_compr
        def while_loop(node):
            value = []
            while context.operators.bool.native(context.eval(node.cond)).__this__:
                value.append(context.eval(node.block))
            return context.wrap(value)
        def if_chain(node):
            if not node.if_blocks:
                raise context.exc.InvalidIfChainEmpty()
            for if_block in node.if_blocks:
                if not if_block.cond:
                    raise context.exc.InvalidIfCondEmpty()
                value = context.eval(if_block.cond)
                if context.operators.bool.native(value).__this__:
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
            # wait whats assign for?
        def stmt_var(node):
            decl = node.vars[0]
            if not node.assign_chain:
                context.declare(decl.id, context.eval(assign.tuple)) # null
                return

            # type = context.eval(decl.type) if decl.type else context.basic_types.Dynamic
            """
                    if stmt.assign_chain:
                        assign = stmt.assign_chain[0]
                        value = context.wrap_code(assign.tuple)
                    type.__fields__[decl.id] = Var(value, type)
            """

            assign = node.assign_chain[0]
            # context.scope[decl.id] = Value(context.eval(assign.tuple))
            context.declare(decl.id, context.eval(assign.tuple))
        def stmt_return(node):
            raise context.exc.Return(context.eval(node.tuple))
        def stmt_import(node):
            source = node.imp.source
            for imp in node.imp.imports:
                path, name = imp.path, imp.name
                if path[-1] == "*":
                    if name:
                        raise ImportError("can't rename all: {} as {}".format(".".join(path), name))
                    module = context.imp(".".join(source + path[:-1]))
                    for name, var in module.__this__.items():
                        context.declare(name, var.value)
                    continue
                module = context.imp(".".join(source + path))
                context.declare(path[-1] if not name else name, module)
                # BEHAVIOR:
                # do import modules DEFINED THERE
                # do import functions DEFINED THERE
                # the intent is to: (maybe ignore floats OR load them as references?)
                #   ignore their imports
        def term_id(node):
            # scope.id
            # sources.id
            # scope.this.id



            id = node.id
            if id in context.scope:
                return context.scope[id]
            #if "this" in context.scope:
            #    this = context.scope["this"]
            #    try:
            #        return context.getattr(this, id)
            #    except AttributeError:
            #        pass
            raise NameError("name {} is not defined".format(repr(id)))
        # t vs e order?
        def term_attr(node):
            obj = context.eval(node.term)
            return context.getattr(obj, node.id) # !!!
        def term_key(node):
            obj = context.eval(node.term)
            key = context.eval(node.tuple)
            return context.operators.getitem.native(obj, key)
        def term_call(node):
            """
                context calls are of (args, kwargs) form, which will fill default[s in
                unpack_args sorts it using the signature into a scope

                arguments in syntax are a list of (id, type, value, pack) objects
                which is neither and needs to be packed first

                *args, **kwargs start existing after becoming scope
                and it's their slots that toggle macro
            """
            args, kwargs = [], {} #t
            eval_args, eval_kwargs = [], {}
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
                elif not arg.pack:
                    args.append(code)
                elif arg.pack == "args":
                    eval_args.extend(context.unwrap(context.eval(code)))
                elif arg.pack == "kwargs":
                    eval_kwargs.update(context.unwrap(context.eval(code))) # iter
            # macro_pack=evals("((*macro args, **macro kwargs) -> args, kwargs)(a.b, key=c * d)", "(macro a.b, macro c * d)"), # prec, interaction with sent *args?

            func = context.eval(node.term)
            func, args = context.callable(func, (args, kwargs))
            scope = context.unpack_args(func, args)
            eval = lambda obj: context.eval(obj) if not arg.macro_ else context.wrap_code(obj)
            for arg in func.args:
                if not arg.pack:
                    if arg.name in scope:
                        scope[arg.name] = eval(scope[arg.name])
                elif arg.pack == "args":
                    pack = [eval(value) for value in scope[arg.name]]
                    if eval_args:
                        if not arg.macro_:
                            pack.extend(eval_args)
                            eval_args = []
                        else:
                            pass # error ,test
                    scope[arg.name] = pack
                elif arg.pack == "kwargs":
                    pack = {name: eval(value) for name, value in scope[arg.name].items()}
                    if eval_kwargs:
                        if not arg.macro_:
                            pack.update(eval_kwargs)
                            eval_kwargs = {}
                        else:
                            pass # error ,test
                    scope[arg.name] = pack
            if eval_args or eval_kwargs:
                pass # error
            return context.call_func(func, scope)
        def term_list(node):
            obj = context.eval(node.tuple)
            if builtins.type(node.tuple).__name__ == "tuple":
                return context.wrap(builtins.list(context.unwrap(obj)))
            else:
                return context.wrap([obj])
        def term_map(node):
            obj = {context.unwrap(context.eval(item.key)): context.eval(item.value) for item in node.map.item_list}
            return context.wrap(obj)
        literal_eval = {
            "null": lambda value: None,
            "boolean": lambda value: value == "true",
            "integer": lambda value: int(value),
            "float": lambda value: float(value),
            "hexadecimal": lambda value: int(value, 16),
            "octal": lambda value: int(value, 8),
            "binary": lambda value: int(value, 2),
            "string": lambda value: value,
            "longstring": lambda value: value,
        }
        def literal(node):
            value = literal_eval[node.type](node.value)
            return context.wrap(value)
            # REASON: constructors send a string literal to native(), causing recursion
            # new looks up __new__ with getattr, which uses call for its args, which wraps values and creates literals
        def tuple(node):
            obj = builtins.tuple(context.eval(expr) for expr in node.expr_list)
            return context.wrap(obj)
        def expr_term(node):
            obj = context.eval(node.term)
            op = context.impl(obj.__type__, "__expr__")
            if op:
                obj = context.call(op, ([obj], {}))
            return obj
        def expr_math(node):
            a = context.eval(node.expr1)
            b = context.eval(node.expr2)
            return context.operators[op_math[node.op]].native(a, b)
        def expr_compare(node):
            a = context.eval(node.expr1)
            b = context.eval(node.expr2)
            return context.operators[op_compare[node.op]].native(a, b)
        def expr_affix(node):
            obj = context.eval(node.term)
            op = None
            if node.op == "++":
                op = increment
            elif node.op == "--":
                op = decrement
            if node.affix == "prefix":
                op(obj)
            result = context.wrap(obj.__this__)
            if node.affix == "postfix":
                op(obj)
            return result
        def expr_bool(node):
            a = context.operators.bool.native(context.eval(node.expr1)).__this__
            b = context.operators.bool.native(context.eval(node.expr2)).__this__
            obj = None
            if node.op == "and":
                obj = a and b
            if node.op == "or":
                obj = a or b
            return context.wrap(obj)
        def expr_not(node):
            obj = context.operators.bool.native(context.eval(node.expr)).__this__
            obj = not obj
            return context.wrap(obj)
        def expr_in(node):
            a = context.eval(node.expr1)
            b = context.eval(node.expr2)
            return context.operators.contains.native(b, a)
        def expr_range(node):
            min = context.eval(node.min)
            max = context.eval(node.max)
            return min # range
        def expr_decorator(node):
            # rename? map a -> b, map_call
            # function retains name
            decorator = context.eval(node.term)
            if not decorator.args[0].macro_:
                obj = context.eval(node.expr)
            else:
                obj = context.wrap_code(node.expr)
            return context.call(decorator, ([obj], {}))
        def expr_macro(node):
            return context.wrap_code(node.code)
        tuple_expr = lambda node: context.eval(node.expr)
        expr_unary = lambda node: context.operators[op_unary[node.op]].native(context.eval(node.expr))
        expr_block = lambda node: context.eval(node.block)
        expr_if = lambda node: context.eval(node.if_chain)
        expr_try = lambda node: context.eval(node.try_chain)
        expr_for = lambda node: context.eval(node.for_loop)
        expr_while = lambda node: context.eval(node.while_loop)
        expr_in_block = lambda node: context.eval(node.in_block)
        expr_func = lambda node: context.eval(node.func_def)
        expr_class = lambda node: context.eval(node.class_def)
        term_literal = lambda node: context.eval(node.literal)
        term_tuple = lambda node: context.eval(node.tuple)

        instructions = dict(locals())
        context.eval = switch(instructions, key=lambda node: builtins.type(node).__name__)
    add_eval()
