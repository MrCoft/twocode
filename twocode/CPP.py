from twocode.Twocode import Twocode
import os

if __name__ == "__main__":

    context = Twocode()

    codebase = os.path.join(os.path.dirname(os.path.dirname(__file__)), "code")
    context.sources.append(codebase)

    #ast = context.parse(open("../code/code/lang/SimpleSample.2c").read())
    #ast = context.parse(open("../code/string/parser/Lexer.2c").read())
    ast = context.parse(open("../code/CPP.2c").read())
    print(ast)

    def map(obj, name=None):
        if isinstance(obj, Func):
            args = []
            for arg in obj.args:
                # uses context
                default_code = repr(context.unwrap_code(arg.default))
                arg_code = arg.name + (":{}".format(arg.type.__name__) if arg.type else "") + (" = {}".format(default_code) if arg.default else "")
                args.append(arg_code)
            block_code = repr(context.unwrap_code(obj.code))
            code = "{} {}({})".format(map_type(obj.return_type), name, ", ".join(args)) + wrap_block(block_code, expand=True)
            return code
        return repr(obj)


    def wrap_block(node, start_block=True, expand=False):
        margin = lambda: " " if start_block else ""
        lines = repr(node).splitlines()
        if not lines:
            return margin() + "{}"
        if len(lines) > 1 or expand:
            return " {{{}\n}}".format("".join("\n" + " " * 4 + line for line in lines))
        else:
            return margin() + lines[0]

    # auto-figure out types
        # the old algo
    # collect imports
        # tag, statement that is removed
        # @include
    # inline a print to the code
        # in a graph, inline a func
    # select impl
        # examples - print, int

    # smart native
    # inline impl - to {}?
    # inline a block {} - free vars from _1

    # native integrated with var names etc

    # @struct

    # id map is kind of broken - we need to add types to it
    # List<Int>

    # module, scope, insert during import, print here, entry="a.b"

    map_format = {
        "type_id": "{id}",
        "type_params": "{id}<{params}>",
        "stmt_tuple": "{tuple}",
        "stmt_break": "break",
        "stmt_continue": "continue",
        "assignment": "{op} {tuple}",
        "tuple_expr": "{expr}",
        "expr_term": "{term}",
        "expr_math": "{expr1} {op} {expr2}",
        "expr_compare": "{expr1} {op} {expr2}",
        "expr_unary": "{op}{term}",
        "expr_bool": "{expr1} {op} {expr2}",
        "expr_if": "{if_chain}",
        "expr_try": "{try_chain}",
        "expr_for": "{for_loop}",
        "expr_while": "{while_loop}",
        "term_id": "{id}",
        "term_access": "{term}.{id}",
        "term_index": "{term}[{tuple}]",
        "term_literal": "{literal}",
        "term_list": "[{tuple}]",
    }
    map_lambda = {
        "code": lambda node: "\n".join(repr(stmt) + ";" for stmt in node.lines),
        "decl": lambda node: "{} {}".format(map_type(repr(node.type.type)), str(node.id)),
        "stmt_var": lambda node: repr(node.vars[0]), # multiple, assign_chain
    }
    def map_term_call(node):
        term = repr(node.term)
        args = repr(node.args)
        if term == "native":
            return eval(args)
        return "{}({})".format(term, args)
    map_lambda["term_call"] = map_term_call
    def repr(node):
        node_type = type(node)
        type_name = node_type.__name__
        print(type_name)
        if type_name in map_format:
            msg = map_format[type_name]
            vars = [var.name for var in node_type.vars]
            return msg.format(**{var: repr(node.__dict__[var]) for var in vars})
        if type_name in map_lambda:
            return map_lambda[type_name](node)
        return str(node)

    map_basic_types = {
        "Int": "int",
    }
    def map_type(type):
        type_name = str(type.__name__) if isinstance(type, Object) else type
        if type is None:
            return "void"
        if type_name in map_basic_types:
            return map_basic_types[type_name]
        return type_name

    context.eval(ast)

    def compile(code):
        main_file = "tc.cpp"
        bin_file = "tc.exe"

        # code = map(obj, "main")
        with open(main_file, "w") as file:
            file.write(code)
        os.system("g++ {} -o {}".format(main_file, bin_file))
        os.system(main_file)
    # compile(context.scope["main"])


    print(code_size(context.scope["main"]))

    code = map(context.scope["main"], "main")
    includes = context.unwrap_value(context.scope["includes"])
    includes_code = "\n".join("#include <{}>".format(path) for path in includes.values())

    code = "\n\n".join([includes_code, code])

    compile(code)

    '''
    map_lambda = {

        "type_func": lambda node: "{}->{}".format(",".join(str(type) for type in node.arg_types), ",".join(str(type) for type in node.return_types)),
        "type_tuple": lambda node: "({})".format(",".join(str(type) for type in node.types)),
        "func_arg": lambda node: pack_args(node.pack) + node.id + (":{}".format(str(node.type)) if node.type else "") + (" = {}".format(str(node.value)) if node.value else ""),
        "call_arg": lambda node: pack_args(node.pack) + ("{}=".format(str(node.id)) if node.id else "") + str(node.value),

        "in_block": lambda node: "in {}:".format(str(node.expr)) + wrap_block(node.block),
        "for_loop": lambda node: "for {} in {}:".format(str(node.var), str(node.iter)) + wrap_block(node.block),
        "while_loop": lambda node: "while {}:".format(str(node.cond)) + wrap_block(node.block),
        "stmt_assign": lambda node: str(node.tuple) + " " + "".join(str(assign) for assign in node.assign_chain),
        "stmt_return": lambda node: "return" + (" " + str(node.tuple) if node.tuple else ""),
        "tuple": lambda node: ", ".join(str(expr) for expr in node.expr_list) + ("," if len(node.expr_list) == 1 else ""),
        "args": lambda node: ", ".join(str(arg) for arg in node.args),
        "expr_affix": lambda node: node.op + str(node.term) if node.affix == "prefix" else str(node.term) + node.op,
        "expr_not": lambda node: "not " + str(node.expr) if not type(node.expr).__name__ == "expr_in" else "{} not in {}".format(str(node.expr.expr1), str(node.expr.expr2)),
        "expr_block": lambda node: wrap_block(node.block, start_block=False),
        "literal": lambda node: node.value if not node.type == "string" else twocode.utils.String.escape(node.value),
    }

    def map_if_chain(node):
        code = ""
        code += "if {}:".format(str(node.if_blocks[0].cond))
        if len(node.if_blocks) == 1 and node.else_block is None:
            code += wrap_block(node.if_blocks[0].block)
            return code
        else:
            code += wrap_block(node.if_blocks[0].block, expand=True)
            for else_if_block in node.if_blocks[1:]:
                code += "\n"
                code += "else if {}:".format(str(else_if_block.cond))
                code += wrap_block(else_if_block.block, expand=True)
            if node.else_block:
                code += "\n"
                code += "else:"
                code += wrap_block(node.else_block, expand=True)
            return code
    map_lambda["if_chain"] = map_if_chain
'''