import copy
from twocode import Utils
import twocode.utils.Nodes
from twocode.utils.Nodes import map, switch, Var, Node
from twocode.utils.Code import filter

class Rule:
    def __init__(self, symbol, pattern):
        self.symbol = symbol
        self.pattern = pattern
    def __repr__(self):
        return "{} -> {}".format(self.symbol, " ".join(self.pattern))

class Grammar:
    def __init__(self):
        self.rules = []
        self.ops = {}
        self.literals = {}
    def form_rules(self):
        self.gen_names()
        prototype_rules = [copy.deepcopy(rule) for rule in self.rules]
        self.apply_list()
        self.apply_cond()
        self.apply_ws()
        self.sub_ws()
        self.apply_cond()
        self.add_ops()
        self.add_literals()
        rules = [Rule(rule.symbol, [symbol.name for symbol in rule.pattern]) for rule in self.rules]
        self.node_types, self.transform = self.gen_transform(prototype_rules, self.rules, rules)
        return rules

    def apply_ws(self):
        """
            modifies rules that have an allow_ws tag
        """
        S = Grammar.Symbol
        for rule in self.rules:
            if rule.allow_ws:
                rule.allow_ws = False
                for i in range(len(rule.pattern)):
                    rule.pattern = rule.pattern[:2 * i] + [S("WS", opt=True)] + rule.pattern[2 * i:]
                rule.pattern = rule.pattern[1:]
    def apply_cond(self):
        """
            generates 2 ^ n rules from rules for each conditional symbol
        """
        result = []
        for rule in self.rules:
            indices = []
            cond_count = 0
            for index, symbol in enumerate(rule.pattern):
                if symbol.opt:
                    symbol.opt = False
                    indices.append(index)
                    cond_count += 1
            for i in range(2 ** cond_count):
                res_rule = copy.deepcopy(rule)
                for index, at in reversed(list(enumerate(indices))):
                    if i & (1 << index):
                        res_rule.pattern.pop(at)
                result.append(res_rule)
        self.rules = result
    def apply_list(self):
        """
            converts rules with list(expr) symbols
        """
        S = Grammar.Symbol
        symbol_scope = set(rule.symbol for rule in self.rules)
        result = []
        for rule in self.rules:
            for symbol in rule.pattern:
                if symbol.list:
                    delim = symbol.list.delim
                    symbol.list = None
                    list_symbol = Utils.free_var(symbol.name + "_list", symbol_scope)
                    symbol_scope.add(list_symbol)
                    delim = [delim] if delim else []
                    rls = [
                        Grammar.Rule([S(symbol.name, var="list")], "list_create", symbol=list_symbol),
                        Grammar.Rule([S(list_symbol, var="first")] + delim + [S(symbol.name, var="second")],
                                         "list_append", allow_ws=rule.allow_ws, symbol=list_symbol)
                    ]
                    for rl in rls:
                        rl.tags.add("list")
                    self.rules.extend(rls)
                    symbol.name = list_symbol
        self.rules.extend(result)
    def sub_ws(self):
        self.add_symbol("WS", [
            Grammar.Rule(pattern, allow_ws=False) for pattern in [
                ["EOL"],
                ["WS", "WS"],
                ["ENTER"], ["LEAVE"],
            ]
        ])
        for rule in self.rules:
            if rule.symbol == "WS":
                rule.symbol = "_WS"
            for symbol in rule.pattern:
                if symbol.name == "WS":
                    symbol.name = "_WS"
        self.add_symbol("_WS", [Grammar.Rule(["WS"])])
    def add_ops(self):
        """
            Map<Tuple<K,V>> parsed '>>' as bit shift
            build operators from characters in grammar
        """
        for symbol, group in self.ops.items():
            for item in group:
                rule = Grammar.Rule(["'" + char + "'" for char in item], symbol=symbol)
                rule.tags.add("op")
                self.rules.append(rule)
    def add_literals(self):
        S = Grammar.Symbol
        rules = [Grammar.Rule([S("LITERAL_" + literal)], literal) for literal in self.literals.keys()]
        self.add_symbol("LITERAL", rules)

    def gen_names(self):
        rule_scope = set()
        for rule in self.rules:
            rule_name = str(rule)
            if rule_name in rule_scope:
                rule.name = "0"
                rule_name = Utils.free_var(str(rule), rule_scope)
                rule.name = rule_name[len(rule.symbol):]
            rule_scope.add(rule_name)
    def gen_transform(self, prototype_rules, rules, rule_copies):
        """
            solved design problems:
                rules like <file> are almost placeholders, a reason for a fallthrough transformation
                    as creating a Node for them would cut the tree
                    but this then breaks a Return node which has no children
        """
        def node_gen(rule):
            vars = []
            for symbol in rule.pattern:
                if symbol.var:
                    var = Var(symbol.var)
                    var.type = symbol.name
                    if var.type not in nonterminals:
                        var.type = None
                    var.list = bool(symbol.list)
                    if symbol.list:
                        var.default = []
                    vars.append(var)
            if not (vars or rule.symbol in used_types):
                return None
            GenNode = twocode.utils.Nodes.node_gen(str(rule), vars)
            return GenNode
        nonterminals = {rule.symbol for rule in prototype_rules}
        used_types = {symbol.name for rule in prototype_rules for symbol in rule.pattern if symbol.var}
        # REASON: discard types that won't be created
        copy_to_rule = {rule_copy: rule for rule, rule_copy in zip(rules, rule_copies)}
        node_types = {}
        node_types["literal"] = twocode.utils.Nodes.node_gen("literal", [Var("value"), Var("type")])
        nonterminals.add("LITERAL")
        for rule in prototype_rules:
            node_type = node_gen(rule)
            if node_type:
                node_types[str(rule)] = node_type
        for node_type in node_types.values():
            for var in node_type.vars:
                if var.type == "LITERAL":
                    var.type = "literal"

        def transform_op(rule):
            if "op" in rule.tags:
                op = "".join(symbol.name[1:-1] for symbol in rule.pattern)
                return lambda node: Node(rule=None, token=op)
            return lambda node: node
        def transform_terminals(node):
            """
                unwraps raw tokens
            """
            return node.token
        def transform_literals(rule):
            node_type = node_types["literal"]
            f = lambda node: node
            if rule.symbol == "LITERAL":
                literal_type = rule.name
                def f(node):
                    return node_type(node.children[0], literal_type)
            return f
        def transform_list(rule):
            """
                collapses list grammars to lists
            """
            f = lambda node: node
            if "list" in rule.tags:
                if rule.name == "list_create":
                    def f(node):
                        return node.children
                if rule.name == "list_append":
                    def f(node):
                        return node.children[0] + [node.children[-1]]
            return f
        def transform_type(rule):
            rule_name = str(rule)
            if rule_name not in node_types:
                return lambda node: node
            node_type = node_types[rule_name]
            assign = {}
            for index, symbol in enumerate(rule.pattern):
                if symbol.var:
                    assign[symbol.var] = index
            def f(node):
                scope = {}
                for var, index in assign.items():
                    scope[var] = node.children[index]
                return node_type(**scope)
            return f

        """
            order matters, we group transformative functions as some create non-nodes

            ops - terminals don't appear in NodeTypes' children

            terminals - turns nodes into strings, can't be followed by switch
            list - turns nodes into lists, which only NodeTypes can handle
            type - requires transformed lists
        """
        token_transform = map(leave=switch({rule: transform_op(rule) for rule in rules},
                                lambda node: copy_to_rule.get(node.rule)))
        type_map = {rule: filter(transform_literals(rule), transform_list(rule), transform_type(rule)) for rule in rules}
        type_map[None] = transform_terminals
        type_transform = map(leave=switch(type_map, lambda node: copy_to_rule.get(node.rule)))
        transform = filter(token_transform, type_transform)
        return node_types, transform

    def add_symbol(self, symbol, rules):
        for rule in rules:
            rule.symbol = symbol
        self.rules.extend(rules)
    class Rule(Rule):
        def __init__(self, pattern, name="", allow_ws=True, symbol=None):
            S = Grammar.Symbol
            self.symbol = symbol
            self.pattern = [symbol if type(symbol) is S else S(symbol) for symbol in pattern]
            self.name = name
            self.allow_ws = allow_ws
            self.tags = set()

        def __str__(self):
            return self.symbol + "_" + self.name if self.name else self.symbol
    class Symbol:
        def __init__(self, name, list=None, opt=False, var=None):
            self.name = name
            self.var = var
            self.opt = opt
            self.list = list
        Var = lambda name: Grammar.Symbol(name, var=name)
        class List:
            def __init__(self, delim=None):
                self.delim = delim

def default_grammar():
    Rule = Grammar.Rule
    S = Grammar.Symbol
    Var = Grammar.Symbol.Var
    List = Grammar.Symbol.List
    grammar = Grammar()

    grammar.add_symbol("file", [
        Rule([S("file_content", list=List(), var="content")])
    ])
    grammar.add_symbol("file_content", [
        Rule([S("class", var="content")])
    ])
    grammar.add_symbol("class", [
        Rule(["'class'", S("id", var="name"), "ENTER", S("class_content", list=List(), var="content"), "LEAVE"])
    ])
    grammar.add_symbol("class_content", [
        Rule([Var("decl")]),
        Rule([Var("func")])
    ])
    grammar.add_symbol("line", [
        Rule([Var("expr")], "expr"),
        Rule([Var("term"), S("ASSIGN", var="op"), Var("expr")], "assign"),
        Rule([Var("decl"), "'='", Var("expr")], "def"),
        Rule([Var("decl")], "decl"),
        Rule(["'return'"], "return"),
        Rule(["'return'", Var("expr")], "returnexpr")
    ])
    grammar.add_symbol("decl", [
        Rule([Var("type"), Var("id")])
    ])
    grammar.add_symbol("type", [
        Rule([Var("id")], "simple"),
        Rule([Var("id"), "'<'", S("type", var="template"), "'>'"], "template")
    ])
    grammar.add_symbol("func", [
        Rule([Var("type"), Var("id"), "'('", S("decl", list=List(delim="','"), opt=True, var="arg_list"), "')'",
              "ENTER", S("line", list=List(), var="code"), "LEAVE"])
    ])
    grammar.add_symbol("expr", [
        Rule([Var("term")], "term"),
        Rule([S("expr", var="expr1"), S("MATH", var="op"), S("expr", var="expr2")], "math"),
        Rule([S("expr", var="expr1"), S("COMPARE", var="op"), S("expr", var="expr2")], "compare"),
        Rule([S("UNARY", var="op"), Var("term")], "unary"),
        Rule([S("FIX", var="op"), Var("term")], "prefix"),
        Rule([Var("term"), S("FIX", var="op")], "postfix")
    ])
    grammar.add_symbol("term", [
        Rule([Var("id")], "id"),
        Rule([S("LITERAL", var="literal")], "literal"),
        Rule([Var("term"), "'('", S("expr", list=List(), opt=True, var="expr_list"), "')'"], "call"),
        Rule([Var("term"), "'['", S("expr", list=List(), opt=True, var="expr_list"), "']'"], "index"),
        Rule([Var("term"), "'.'", Var("id")], "access"),
        Rule(["'('", S("expr", list=List(), opt=True, var="expr"), "')'"], "parens"),
        Rule(["'['", S("expr", list=List(), opt=True, var="expr_list"), "']'"], "array")
    ])

    return grammar

if __name__ == "__main__":
    import Lexer

    lex_lang = Lexer.default_lex()
    lex_model = lex_lang.form_model()
    lexer = lex_model.form_lexer()

    grammar = default_grammar()
    grammar.ops = lex_lang.ops
    grammar.literals = lex_lang.literals
    rules = grammar.form_rules()
    for rule in rules:
        print(rule)