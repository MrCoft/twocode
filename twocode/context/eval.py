from twocode import utils
from twocode.utils.node import switch
import builtins
from twocode.context.operators import op_assign, op_compare, op_math, op_unary, keyword_ops, increment, decrement
from twocode.context.basic_types import literal_eval
import twocode.utils.string

def add_eval(context):
    def code(node):
        for stmt in node.lines[:-1]:
            context.eval(stmt, type="stmt")
        if node.lines:
            value = context.eval(node.lines[-1], type="pass")
            return value
    def type_id(node):
        return context.scope[node.id]
    def type_params(node):
        for param in node.params.args: # too much
            # call_arg. func_def does that manually
            type = context.eval(param, type="expr")
        return context.scope[node.id]
    def type_func(node):
        for type_node in node.arg_types:
            type = context.eval(type_node, type="expr")
        for type_node in node.return_types:
            type = context.eval(type_node, type="expr")
        # return what
    def type_tuple(node):
        for type_node in node.types:
            type = context.eval(type_node, type="expr")
        # return what
    def func_def(node):
        func = context.obj.Func()
        level = 0
        for arg in node.args:
            arg_pack = context.pack_level(arg.pack, arg.id)
            if arg_pack < level:
                raise context.exc.InvalidPack()
            else:
                level = arg_pack

            func_arg = context.obj.Arg()
            func_arg.name = arg.id
            func_arg.type = context.eval(arg.type, type="expr")
            func_arg.default_ = arg.default
            func_arg.pack = arg.pack
            func_arg.macro_ = arg.macro
            func.args.append(func_arg)
        func.return_type = context.eval(node.return_type, type="expr")
        func.code = node.block
        func.frame = context.scope.frame_copy()

        func = context.obj.Ref(func, context.objects.Func)
        if node.id:
            context.declare(node.id, func, context.objects.Func)
        value = func
        if node.id:
            value = context.stmt_value(value)
        return value
    def class_def(node):
        # func.scope = context.scope.copy()
        # not saving for every func is efficient, but actually shouldnt be done
        # what context for the macros?
        # and what about outside, patched funcs/vars?
        cls = context.obj.Class()
            # i've seen a for loop used in custom 2c code, one that generates variables
            # why did we leave the "exec in class" paradigm again?
        if node.base:
            cls.__base__ = context.eval(node.base, type="expr")
        for stmt in node.block.lines:
            type_name = type(stmt).__name__
            if type_name == "stmt_var":
                decl = stmt.declares.decl # syntax error
                attr = context.obj.Attr()
                attr.type = context.eval(decl.type, type="expr") if decl.type else context.basic_types.Object
                if stmt.assign_chain:
                    assign = stmt.assign_chain[0]
                    attr.default_ = assign.tuple # fk
                cls.__fields__[decl.id] = attr
                continue
            elif type_name == "stmt_tuple":
                stmt = stmt.tuple.expr
                type_name = type(stmt).__name__
                if type_name == "expr_func":
                    stmt = stmt.func_def
                    func = context.obj.Func()
                    if not stmt.id:
                        raise SyntaxError("anonymous function in class definition")
                    cls.__fields__[stmt.id] = func
                    func.args.append(context.obj.Arg("this", cls))
                    for arg in stmt.args:
                        func_arg = context.obj.Arg()
                        func_arg.name = arg.id
                        func_arg.type = context.eval(arg.type, type="expr")
                        func_arg.default_ = arg.default
                        func_arg.pack = arg.pack
                        func_arg.macro_ = arg.macro
                        func.args.append(func_arg)
                    func.return_type = context.eval(stmt.return_type, type="expr")
                    func.code = stmt.block
                    func.frame = context.scope.frame_copy()
                    continue
            raise SyntaxError("invalid statement in class definition")
        cls.__frame__ = context.scope.frame_copy()

        cls = context.obj.Ref(cls, context.objects.Class)
        if node.id:
            context.declare(node.id, cls, context.objects.Class)
        value = cls
        if node.id:
            value = context.stmt_value(value)
        return value
    def if_chain(node):
        if not node.if_blocks:
            raise context.exc.InvalidIfChainEmpty()
        for if_block in node.if_blocks:
            if not if_block.expr:
                raise context.exc.InvalidIfCondEmpty()
            value = context.eval(if_block.expr, type="expr")
            if context.operators.bool.native(value).__this__:
                with context.ScopeContext():
                    value = context.eval(if_block.block, type="pass")
                    value = context.stmt_value(value)
                    return value
        if node.else_block:
            with context.ScopeContext():
                value = context.eval(node.else_block, type="pass") # consistent Null?
                value = context.stmt_value(value)
                return value
    def for_loop(node):
        iter = context.eval(node.expr, type="expr")
        iter = context.operators.iter.native(iter)
        has_next = context.impl(iter.__type__, "has_next")
        next = context.impl(iter.__type__, "next")

        def expand_name(node, value):
            type_name = type(node).__name__
            if type_name == "multiple_id":
                id = node.id
            elif type_name == "multiple_id_tuple":
                if value:
                    iter = context.operators.iter.native(value)
                    list = context.call(context.impl(context.basic_types.List, "from_iter"), ([iter], {}))
                    list = context.unwrap(list)
                    if len(list) < len(node.names):
                        raise ValueError("too many values to unpack (expected {}, got {})".format(len(node.names), len(list)))
                    if len(list) > len(node.names): # msg should not be recursive - give specific names
                        raise ValueError("not enough values to unpack (expected {}, got {})".format(len(node.names), len(list)))
                    for name, item in zip(node.names, list):
                        item = context.operators.expr.native(item)
                        expand_name(name, item)
                else:
                    for name in node.names:
                        expand_name(name, None)
                return # value?
                # else error
            context.declare(id, value, value.__reftype__)

        compr = []
        while True:
            if not context.call(has_next, ([iter], {})).__this__:
                break
            try:
                with context.ScopeContext():
                    expand_name(node.names, context.call(next, ([iter], {})))
                    item = context.eval(node.block, type="expr")
                    compr.append(item)
            except context.exc.Break:
                break
            except context.exc.Continue:
                continue
        value = context.wrap(compr)
        value = context.stmt_value(value)
        return value
    def while_loop(node):
        compr = []
        while context.operators.bool.native(context.eval(node.expr, type="expr")).__this__:
            try:
                with context.ScopeContext():
                    compr.append(context.eval(node.block, type="expr"))
            except context.exc.Break:
                break
            except context.exc.Continue:
                continue
        value = context.wrap(compr)
        value = context.stmt_value(value)
        return value
    def stmt_break(node):
        raise context.exc.Break()
    def stmt_continue(node):
        raise context.exc.Continue() # syntax error? loop context?
    def with_block(node):
        obj = context.eval(node.expr, type="expr")
        enter = context.impl(obj.__type__, "enter")
        leave = context.impl(obj.__type__, "leave")
        context.call(enter, ([obj], {}))
        try:
            with context.ScopeContext():
                if node.id:
                    context.declare(node.id, obj, obj.__reftype__)
                value = context.eval(node.block, type="pass")
                value = context.stmt_value(value)
                return value
        finally:
            context.call(leave, ([obj], {}))
    def in_block(node):
        obj = context.eval(node.expr, type="expr")
        value = context.operators.eval.native(node.block, scope=obj)
        if node.id:
            context.declare(node.id, obj, obj.__reftype__)
        value = context.stmt_value(value)
        return value
    def stmt_tuple(node):
        return context.eval(node.tuple, type="pass")
    def stmt_assign(node):
        assign = node.assign_chain[0]
        op = op_assign[assign.op]
        node = node.terms

        inplace = op != "mov"
        def expand_assign(node, value):
            type_name = type(node).__name__
            if type_name == "multiple_term":
                node = node.term
            elif type_name == "multiple_term_tuple":
                iter = context.operators.iter.native(value)
                list = context.call(context.impl(context.basic_types.List, "from_iter"), ([iter], {}))
                list = context.unwrap(list)
                if len(list) < len(node.terms):
                    raise ValueError("too many values to unpack (expected {}, got {})".format(len(node.terms), len(list)))
                if len(list) > len(node.terms): # msg should not be recursive - give specific names
                    raise ValueError("not enough values to unpack (expected {}, got {})".format(len(node.terms), len(list)))
                for term, item in zip(node.terms, list):
                    item = context.operators.expr.native(item)
                    expand_assign(term, item)
                return # value?

            type_name = type(node).__name__
            if type_name == "term_id":
                if inplace:
                    obj = context.scope[node.id] # var.type
            if type_name == "term_attr":
                lvalue = context.eval(node.term, type="term")
                if inplace:
                    obj = context.getattr(lvalue, node.id)
            if type_name == "term_key":
                lvalue = context.eval(node.term, type="term")
                key = context.eval(node.tuple, type="expr")
                if inplace:
                    obj = context.operators.getitem.native(lvalue, key)

            while True:
                if inplace:
                    impl = context.impl(obj.__type__, "__{}__".format(op))
                    if impl:
                        context.call(impl, ([obj, value], {}))
                        value = obj
                        break
                    value = context.operators[keyword_ops.get(op[1:], op[1:])].native(obj, value)
                    value = context.operators.expr.native(value)
                    impl = context.impl(obj.__type__, "__mov__")
                    if impl:
                        context.call(impl, ([obj, value], {}))
                        value = obj
                        break
                if type_name == "term_id":
                    context.scope[node.id] = value
                if type_name == "term_attr":
                    context.setattr(lvalue, node.id, value)
                if type_name == "term_key":
                    context.operators.setitem.native(lvalue, key, value)
                break

            return value

        value = context.eval(assign.tuple, type="expr")
        value = expand_assign(node, value)
        value = context.stmt_value(value)
        return value
    def stmt_var(node):
        # assign chain!
        def expand_var(node, value):
            type_name = builtins.type(node).__name__
            if type_name == "multiple_decl":
                decl = node.decl
            elif type_name == "multiple_decl_tuple":
                if value:
                    iter = context.operators.iter.native(value)
                    list = context.call(context.impl(context.basic_types.List, "from_iter"), ([iter], {}))
                    list = context.unwrap(list)
                    if len(list) < len(node.declares):
                        raise ValueError("too many values to unpack (expected {}, got {})".format(len(node.declares), len(list)))
                    if len(list) > len(node.declares): # msg should not be recursive - give specific names
                        raise ValueError("not enough values to unpack (expected {}, got {})".format(len(node.declares), len(list)))
                    for decl, item in zip(node.declares, list):
                        item = context.operators.expr.native(item)
                        expand_var(decl, item)
                else:
                    for decl in node.declares:
                        expand_var(decl, value)
                return # value?
                # else error
            # convert?
            type = context.eval(decl.type) if decl.type else value.__reftype__
            context.declare(decl.id, value, type)
            # var x?

        if node.assign_chain:
            value = context.eval(node.assign_chain[0].tuple, type="expr")
        else:
            value = context.wrap(None)
        value = expand_var(node.declares, value)
        value = context.stmt_value(value)
        return value
    def stmt_return(node):
        raise context.exc.Return(context.eval(node.tuple, type="expr"))
    def stmt_import(node):
        source = node.imp.source
        for imp in node.imp.imports:
            path, id = imp.path, imp.id
            if path[-1] == "*":
                if id:
                    raise ImportError("can't rename all: {} as {}".format(".".join(path), id))
                module = context.imp(".".join(source + path[:-1]))
                for name, var in module.__this__.items():
                    context.declare(name, var.value, var.type)
                continue
            module = context.imp(".".join(source + path))
            context.declare(path[-1] if not id else id, module, module.__reftype__)
            # BEHAVIOR:
            # do import modules DEFINED THERE
            # do import functions DEFINED THERE
            # the intent is to: (maybe ignore floats OR load them as references?)
            #   ignore their imports
    def expr_math(node):
        a = context.eval(node.expr1, type="expr")
        b = context.eval(node.expr2, type="expr")
        op = op_math[node.op]
        op = keyword_ops.get(op, op)
        return context.operators[op].native(a, b)
    def expr_compare(node):
        a = context.eval(node.expr1, type="expr")
        b = context.eval(node.expr2, type="expr")
        op = op_compare[node.op]
        return context.operators[op].native(a, b)
    def expr_affix(node):
        obj = context.eval(node.term, type="expr")
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
        a = context.operators.bool.native(context.eval(node.expr1, type="expr")).__this__
        eval_b = lambda: context.operators.bool.native(context.eval(node.expr2, type="expr")).__this__
        obj = None
        if node.op == "and":
            obj = a and eval_b()
        if node.op == "or":
            obj = a or eval_b()
        return context.wrap(obj)
    def expr_not(node):
        obj = context.operators.bool.native(context.eval(node.expr, type="expr")).__this__
        obj = not obj
        return context.wrap(obj)
    def expr_in(node):
        a = context.eval(node.expr1, type="expr")
        b = context.eval(node.expr2, type="expr")
        return context.operators.contains.native(b, a)
    def expr_range(node):
        min = context.eval(node.min, type="expr")
        max = context.eval(node.max, type="expr")
        return min # range
    def expr_decorator(node):
        # rename? map a -> b, map_call
        # function retains name
        # has to work on callable, so we can stack wrappers!!!!!
        decorator = context.eval(node.term, type="expr")
        if not decorator.args[0].macro_:
            obj = context.eval(node.expr, type="expr")
        else:
            obj = context.wrap_code(node.expr)
        return context.call(decorator, ([obj], {}))
    def expr_macro(node):
        code_type = context.parser.node_types["code"]
        return context.wrap_code(code_type([node.stmt]))
    def term_id(node):
        id = node.id
        if id in context.scope:
            return context.scope[id]
        raise NameError("name {} is not defined".format(twocode.utils.string.escape(id)))
    def term_attr(node):
        obj = context.eval(node.term, type="term")
        return context.getattr(obj, node.id)
    def term_key(node):
        obj = context.eval(node.term, type="term")
        key = context.eval(node.tuple, type="expr")
        return context.operators.getitem.native(obj, key)
    def literal(node):
        value = literal_eval[node.type](node.value)
        return context.wrap(value)
        # REASON: constructors send a string literal to native(), causing recursion
        # new looks up __new__ with getattr, which uses call for its args, which wraps values and creates literals
    def term_call(node):
        """
            context calls are of (args, kwargs) form, which will fill defaults in
            unpack_args sorts it using the signature into a scope

            arguments in syntax are a list of (id, type, value, pack) objects
            which is neither and needs to be packed first

            *args, **kwargs start existing after becoming scope
            and it's their slots that toggle macro
        """
        # wat
        func = context.eval(node.term, type="term")

        args, kwargs = [], {}
        val_args, val_kwargs = [], {}
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
                val_args.extend(context.unwrap(context.eval(code, type="expr")))
            elif arg.pack == "kwargs":
                val_kwargs.update(context.unwrap(context.eval(code, type="expr")))

            # iter - yeah, accept even a generator. convert to list/map!

            # order though

        # macro_pack=evals("((*macro args, **macro kwargs) -> args, kwargs)(a.b, key=c * d)", "(macro a.b, macro c * d)"), # prec, interaction with sent *args?

        # so do we just ignore val or what?
        func, args = context.callable(func, (args, kwargs))
            # callable is weird. it just prepends some args
        scope = context.unpack_args(func, args)
        eval = lambda obj: context.eval(obj, type="expr") if not arg.macro_ else context.wrap_code(obj)
        for arg in func.args:
            if not arg.pack:
                if arg.name in scope:
                    scope[arg.name] = eval(scope[arg.name])
            elif arg.pack == "args":
                pack = [eval(value).__refobj__ for value in scope[arg.name]]
                if val_args:
                    if not arg.macro_:
                        pack.extend([value.__refobj__ for value in val_args])
                        val_args = []
                    else:
                        pass # error ,test
                scope[arg.name] = pack
            elif arg.pack == "kwargs":
                pack = {name: eval(value).__refobj__ for name, value in scope[arg.name].items()}
                if val_kwargs:
                    if not arg.macro_:
                        pack.update({name: value.__refobj__ for name, value in val_kwargs.items()})
                        val_kwargs = {}
                    else:
                        pass # error ,test
                scope[arg.name] = pack
        if val_args or val_kwargs:
            pass # error
        # macro args not working right now
        return context.call_func(func, scope)
    def tuple(node):
        obj = builtins.tuple(context.eval(expr, type="expr").__refobj__ for expr in node.expr_list)
        return context.wrap(obj)
    def term_list(node):
        obj = context.eval(node.tuple, type="expr") # the items, yes, not the term
        if type(node.tuple).__name__ == "tuple":
            return context.wrap(builtins.list(context.unwrap(obj)))
        else:
            return context.wrap([obj.__refobj__])
    def term_map(node):
        obj = {context.unwrap(context.eval(item.key, type="expr")): context.eval(item.value, type="expr") for item in node.map.item_list}
        return context.wrap(obj)
    tuple_expr = lambda node: context.eval(node.expr, type="pass")
    expr_term = lambda node: context.eval(node.term, type="pass")
    expr_unary = lambda node: context.operators[op_unary[node.op]].native(context.eval(node.expr))
    expr_block = lambda node: context.eval(node.block, type="pass") # has scope?
    expr_if = lambda node: context.eval(node.if_chain, type="pass")
    expr_for = lambda node: context.eval(node.for_loop, type="pass")
    expr_while = lambda node: context.eval(node.while_loop, type="pass")
    expr_with_block = lambda node: context.eval(node.with_block, type="pass")
    expr_in_block = lambda node: context.eval(node.in_block, type="pass")
    expr_func = lambda node: context.eval(node.func_def, type="pass")
    expr_class = lambda node: context.eval(node.class_def, type="pass")
    term_literal = lambda node: context.eval(node.literal, type="pass")
    term_tuple = lambda node: context.eval(node.tuple, type="pass")
    # which nodes don't return?
    # import, types, possibly assigns
    # make vars and assigns return None?

    context.instructions = utils.redict(locals(), "context".split())
    context.eval_pass = switch(context.instructions, key=lambda node: type(node).__name__)
    def eval(node, type="expr"):
        obj = context.eval_pass(node)
        if obj is None or not isinstance(obj, context.obj.Ref):
            return # context.obj.Ref(context.basic_types.Null)

        """
            SYNTACTIC OPERATORS

            operators tell us what happens to an object
                e.g. "x + y" is add(x, y)
            syntactic operators allow us to know when nothing happens to it
                e.g. "x" is stmt(x), "y = x" is "y = expr(x)"

            calling syntax ops on expr_term, stmt_expr doesn't work
            an object can go through several such nodes,
            we would need to know when it becomes an expr
            and DOESN'T become a stmt to call its __expr__,
            defeating the ops' purpose of being triggered by lack of events

            instead of when it is passed, these operators need to be called
            when the object is USED, when it leaves syntactic manipulation
        """
        if type == "term":
            impl = context.impl(obj.__type__, "__term__")
            if impl:
                obj = context.call(impl, ([obj], {}))
        if type == "expr":
            impl = context.impl(obj.__type__, "__expr__")
            if impl:
                obj = context.call(impl, ([obj], {}))
        if type == "stmt":
            impl = context.impl(obj.__type__, "__stmt__")
            if impl:
                obj = context.call(impl, ([obj], {}))

        return obj
    context.eval = eval
