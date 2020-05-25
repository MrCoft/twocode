import twocode.utils.string
from twocode.utils.interface import Table

LOG = set()
# LOG.add("DEBUG")

class TypeInfer:
    def __init__(self, transp):
        self.node_type = {}
        transp.type_infer = self
        transp.node_type = self.node_type

        self.gen_type_ops()

    def gen_type_ops(self):
        node_type = self.node_type
        from . import import_code_env
        import_code_env()

        class type_op:
            def __init__(self, node):
                self.node = node
            def attempt(self):
                pass
            def msg(self):
                pass

        class type_op_code(type_op):
            def attempt(self):
                if not self.node.lines:
                    node_type[self.node] = Null
                    return
                type = node_type[self.node.lines[-1]]
                if type:
                    node_type[self.node] = type
        class type_op_term_id(type_op):
            def __init__(self, node):
                super().__init__(node)
                self.scope = None
                self.fail = False
            def attempt(self):
                if self.fail:
                    return
                id = self.node.id
                if not self.scope:
                    scope = transp.node_to_scope[self.node]
                    while scope:
                        if id in scope.vars:
                            self.scope = scope
                            break
                        scope = scope.parent
                    if not scope:
                        self.fail = True
                        return
                type = self.scope.vars[id].type
                if type:
                    node_type[self.node] = type
            def msg(self):
                if self.fail:
                    return "can't resolve name {}".format(twocode.utils.string.escape(self.node.id))
                #
        class type_op_literal(type_op):
            literal_eval = {
                "null": Null,
                "boolean": Bool,
                "integer": Int,
                "float": Float,
                "string": String,
            }
            def attempt(self):
                node_type[self.node] = type_op_literal.literal_eval[self.node.type]
        class type_op_term_attr(type_op):
            def __init__(self, node):
                super().__init__(node)
                self.scope = None
                self.fail = False
            def attempt(self):
                if self.fail:
                    return
                type = node_type[self.node.term]
                if not type:
                    return
                field = type.__fields__.get(self.node.id)
                if not field:
                    self.fail = True
                # if field(scope) is typed, type
            def msg(self):
                if self.fail:
                    return "invalid attribute: {} of {}".format(self.node.id, c.operators.qualname.native(node_type[self.node.term]))
            # not used?

        def pass_type_op(attr):
            class type_op_pass(type_op):
                def attempt(self):
                    node = getattr(self.node, attr)
                    type = node_type[node]
                    if type:
                        node_type[self.node] = type
            return type_op_pass
        def const_type_op(type):
            class type_op_const(type_op):
                def attempt(self):
                    node_type[self.node] = type
            return type_op_const
            # a single one? why return when we can check?
        self.op_map = {
            "code": type_op_code,
            "stmt_tuple": pass_type_op("tuple"),
            "stmt_return": const_type_op(Null),
            "tuple_expr": pass_type_op("expr"),
            "expr_term": pass_type_op("term"),
            "expr_bool": const_type_op(Bool),
            "expr_not": const_type_op(Bool),
            "expr_in": const_type_op(Bool),
            "expr_if": pass_type_op("if_chain"),
            "expr_for": pass_type_op("for_loop"),
            "expr_while": pass_type_op("while_loop"),
            "expr_try": pass_type_op("try_chain"),
            "expr_with_block": pass_type_op("with_block"),
            "expr_in_block": pass_type_op("in_block"),
            "term_id": type_op_term_id,
            "term_literal": pass_type_op("literal"),
            "literal": type_op_literal,
            "tuple": const_type_op(Tuple),
            "term_list": const_type_op(List),
        }

    def infer(self):
        from . import import_code_env
        import_code_env()

        for node in transp.all_nodes:
            type_name = type(node).__name__
            if type_name not in "if_block".split(): # wat
                self.node_type[node] = None

        self.typing_ops = []
        if "DEBUG" in LOG: self.undef_node_types = []
        for node in transp.all_nodes:
            if not node in self.node_type:
                continue
            type_name = type(node).__name__
            if type_name in self.op_map:
                self.typing_ops.append(self.op_map[type_name](node))
            elif "DEBUG" in LOG:
                if type_name not in self.undef_node_types:
                    self.undef_node_types.append(type_name)

        print("Inferring types:")
        repeat = True
        i = 1
        while repeat:
            print("pass {} - {} left".format(i, len(self.typing_ops)))
            typing_ops_re = []
            for type_op in self.typing_ops:
                type_op.attempt()
                if not self.node_type[type_op.node]:
                    typing_ops_re.append(type_op)
            repeat = len(self.typing_ops) - len(typing_ops_re) > 0
            self.typing_ops = typing_ops_re
            i += 1
        print()

    def summary(self):
        from . import import_code_env
        import_code_env()

        print("Typing results:")

        total = sum(len(scope.vars) for scope in transp.all_scopes)
        print(total, "names total", end="")
        left = total - len([type for scope in transp.all_scopes for type in scope.vars.values() if type])
        if left:
            print(",", left, "not typed", end="")
        print()

        total = len(self.node_type)
        print(total, "nodes total", end="")
        left = total - len([type for type in self.node_type.values() if type])
        if left:
            print(",", left, "not typed", end="")
        print()

        print()

        if self.typing_ops:
            print("Errors({}):".format(len(self.typing_ops)))
            table = Table(attrs=[
                ("Type", lambda op: type(op.node).__name__),
                ("Context", lambda op: transp.node_to_scope[op.node].full_desc()[:50]),
                ("Code", lambda op: repr(op.node).splitlines()[0][:25]),
                ("Message", lambda op: op.msg()),
            ])
            print()
            table.data = self.typing_ops
            print(table)
            print()

        if "DEBUG" in LOG and self.undef_node_types:
            print("Can't type node types:")
            print(", ".join(self.undef_node_types))
            print()

        def print_scope(scope, level=0):
            if scope.desc:
                print(" " * level + scope.desc + ":") #
                level += 1
            for child in scope.children:
                print_scope(child, level)
        # print_scope(transp.all_scopes[0])

        for op in self.typing_ops:
            scope = transp.node_to_scope[op.node]

        # shared path - scopes. i mean that's the only thing
        # item by item
        # some sort of buffer?

        """
        a.b.c
        a.b.c.d.e

        ->

        a.b.c
        |____d.e




        a.b.c
        a.b.d

        ->

        a.b:
        |____c
        |____d

        or only for certain length? yes for a.b.c.d (: e.f, g.h)
        not for a.b, a.c


        a.f
        a.b.c.d
        a.b.c.e

        ->

        a:
        |____f
        |____b.c:
        | |____d
        | |____e

        do extract a from all
        b.c turns into the problem above




        a.b
        a.b.c.d
        a.b.c.e

        a.b
        |____c.d
        |____c.e

        definitely not c:
        i mean, if a is present, it's cheap to present it AND branch off
        why a though, based on what heuristic
        i guess even though it's short, it's present in 3 items?

        okay, enough times, some total string length, sure, BUT
        since we are already extracting b, which they are children of:
        it's cheaper to a. that





        solve nested problems recursively. don't extract a letter
        if it's short to write

        always extract if the line itself is used

        solve common of multiple lines based on a heuristic:
        e.g 3 times - always extract, or some total string length

        but, don't extract if it's cheaper to prepend a. in front of all parents



        suppose i have x names with some common core
        i extract that core if

        algo:
        1. start with full tree structure, remove nodes
        2. repeatedly extract things from the right
            extraction =
            "a.b.c"
            "a.b.c"
            ->
            a.b.c: ["", ""]

            longest is 5?
            start with 5, 4
            all the same 5s turn into one
                if there IS a 4, the 5 becomes a child of the 4
                as it should be, since it's its direct parent
            now the several 5 are a single-element child
            no, it's just a single entry

            eventually, say you extract 3.
            now, the next shared one is 1
            do extract it if it fits the heuristic

            if you unpack Game, maybe you can't unpack ABC now,
            now that Game.ABC is super long and it's not worth it
            to write that 3 times

            but if we had game, we could have ABC.main, ABC.e, ABC.f


            from the right
        """

        # does the table work properly?
        # are we minimizing chars not shown?
        # if all are 5 and one is 50 i dont want
        # to include extra spaces
        # but if we always cut something, thats stupid
        # shoulnt a richer column receive width at a faster pace?

# for_loop, if_chain
# attr from type/default
# fields to type ops
# func from a return statement

# also ofc: don't show dependent errors
