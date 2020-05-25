import copy
from twocode import utils
import twocode.utils.node
from twocode.utils.node import Node, compact_node, compact_block
from twocode.utils.node import map, switch, Var
from twocode.utils.code import filter

LOG = set()
# LOG.add("DEBUG")
# LOG.add("PERF")

class Parser:
    """
        INEFFICIENCY:
        grammar.py implements "allow_ws" by creating copies of rules interleaved with WS
        for the largest, 12 token long rules, this creates 2048 rules

        STATE PARSER:
        a different algorithm, does not use simple sequences
        each symbol now has a "next" integer and an optional "skip" integer
        accepting this symbol adds "next" to the position
        if "skip" isn't None, we can add it and accept the symbol there instead

        opt, allow_ws and also lists can be implemented this way

        SURPRISES:
        skipping lookup table isn't that simple, it can skip outside if it ends with an optional sequence
        so we allow several symbols and complete the rule at the same time

        the grammar has L-recursion: _WS -> _WS _WS, expr_math and expr_compare
        it would start infinite branches, but the caching system makes it its own parent instead
        it works perfectly because completed matches build copies of their parents,
        creating possibly infinite _WS -> _WS _WS reduction backwards

        a "func" shows twice in the tree on an ID token because it can be either type or type<params>
    """
    def __init__(self, rules):
        self.rules = rules
        self.symbol_rules = {}
        for rule in self.rules:
            self.symbol_rules.setdefault(rule.symbol, []).append(rule)
        self.edge = []
        self.matches = []
        if "PERF" in LOG:
            self.log = utils.Object(
                edge=[],
                reduce_volume=[],
                tree_size=[],
                time=[],
            )
    """
        REASON:
        an abstraction over tree construction
        the transformation works as a (iter_pos, iter_children) -> node
        function, we store the args and build when done
    """
    @staticmethod
    def create_nonterminal(rule):
        return Node(rule=rule, children_pos=[])
    @staticmethod
    def create_terminal(type, token):
        return Node(rule=None, token=token)
    @staticmethod
    def add_child(rule, parent, pos, child):
        parent.children_pos.append(pos)
        parent.children.append(child)
    @staticmethod
    def copy_node(node):
        node_copy = copy.copy(node)
        node_copy.children_pos = node.children_pos.copy()
        return node_copy
    def init_search(self, symbol=None):
        if symbol is None: symbol = self.rules[0].symbol
        self.edge = []
        for rule in self.symbol_rules[symbol]:
            match = Parser.Match([], rule)
            match.node = Parser.create_nonterminal(rule)
            self.edge.append(match)
        self.reduce()
        self.matches = []
        if "PERF" in LOG: self.log.reduce_volume.pop()
    def match(self):
        if self.matches:
            return self.matches[0]
        elif self.possible():
            return None
        else:
            raise Parser.NoMatch()
    class NoMatch(Exception):
        def __str__(self):
            return "match not possible"
    class Match:
        def __init__(self, parents, rule):
            self.parents = parents
            self.rule = rule
            self.pos = 0
            self.node = None
        def __deepcopy__(self, memo):
            # deepcopy of node
            match = Parser.Match(copy.deepcopy(self.parents, memo=memo), self.rule)
            match.pos = self.pos
            copy_node = lambda node: Node(rule=node.rule, children=[copy_node(child) for child in node.children], **utils.redict(node.__dict__, "rule children".split()))
            match.node = copy_node(self.node)
            return match

        def __str__(self):
            lines = [
                "rule: {}".format(self.rule),
                "pos: {}".format(self.pos),
            ]
            lines += ("node:" + compact_block(self.node, delim=Parser.Match.delim)).splitlines()
            if self.parents:
                lines.append("parents:")
                for item in Parser.Match.enum_func(self):
                    for line in item.splitlines():
                        lines.append(Parser.Match.delim + line)
            else:
                lines.append("parents: []")
            return ("\n" + Parser.Match.delim).join(["match:"] + lines)
        delim = ".\t".replace("\t", " " * (4 - 1))
        def parents_str(self):
            return compact_node(self, Parser.Match.name_func, Parser.Match.enum_func)
        @staticmethod
        def name_func(match):
            return "{}[{}]".format(match.rule.name, match.pos)
        @staticmethod
        def enum_func(match):
            return [parent.parents_str() for parent in match.parents if match not in parent.parents]
            # REASON: L-recursion
    def reduce(self):
        if "DEBUG" in LOG: print("Reduce:")
        if "PERF" in LOG: volume = 0
        edge = self.edge
        self.edge = []
        self.matches = []
        while edge:
            if "DEBUG" in LOG: print("\tReducing {} matches:".format(len(edge)))
            if "PERF" in LOG: volume += len(edge)
            edge_re = []
            for match in edge:
                if match.pos > len(match.rule.pattern):
                    raise Exception("algorithm error")

                if match.pos < len(match.rule.pattern):
                    reduces = []
                    for symbol, pos in match.rule.lookup[match.pos].table.items():
                        skip_match = Parser.Match(match.parents, match.rule)
                        skip_match.pos = pos
                        skip_match.node = Parser.copy_node(match.node)
                        self.edge.append(skip_match)
                    if match.rule.lookup[match.pos].skips_out:
                        reduce_match = Parser.Match(match.parents, match.rule)
                        reduce_match.pos = pos + match.rule.pattern[pos].skip
                        reduce_match.node = Parser.copy_node(match.node)
                        reduces.append(reduce_match)
                else:
                    reduces = [match]

                for reduce_match in reduces:
                    if not reduce_match.parents:
                        self.matches.append(reduce_match.node)
                    else:
                        if "DEBUG" in LOG:
                            print("\t\tComplete:")
                            print("\t\t\tRule:", reduce_match.rule)
                            print("\t\t\tParents:")
                            group = []
                        for parent in reduce_match.parents:
                            parent_match = Parser.Match(parent.parents, parent.rule)
                            parent_match.node = Parser.copy_node(parent.node)
                            Parser.add_child(parent.rule, parent_match.node, parent.pos, reduce_match.node)
                            parent_match.pos = parent.pos + parent.rule.pattern[parent.pos].next
                            if "DEBUG" in LOG: group.append("{}[{}]".format(parent.rule.name, parent.pos))
                            edge_re.append(parent_match)
                        if "DEBUG" in LOG: print("\t\t\t\t" + " ".join(group))

            edge = edge_re
        if "DEBUG" in LOG: print()
        edge = self.edge
        self.edge = []
        shared_gen = {}
        if "DEBUG" in LOG: print("Expand:")
        while edge:
            if "PERF" in LOG: volume += len(edge)
            edge_re = []
            for match in edge:
                # if "DEBUG" in LOG: print("\t" + "{}[{}] -> {}".format(match.rule.symbol, match.pos, match.rule.pattern[match.pos].name)) # maybe the [1,]
                symbol = match.rule.pattern[match.pos].name
                if symbol in self.symbol_rules: # for completeness, does this not assume that they are all pos1+? what if the sought symbol was loopy
                    if symbol not in shared_gen:
                        shared_gen[symbol] = []
                        for rule in self.symbol_rules[symbol]:
                            for shared_symbol, shared_pos in rule.lookup[0].table.items():
                                shared_match = Parser.Match([], rule)
                                shared_match.pos = shared_pos
                                shared_match.node = Parser.create_nonterminal(rule)
                                shared_gen[symbol].append(shared_match)
                        edge_re.extend(shared_gen[symbol])
                    for shared_match in shared_gen[symbol]:
                        shared_match.parents.append(match)
                else:
                    # print(match)
                    self.edge.append(match)
            edge = edge_re
        if "DEBUG" in LOG: print()
        if "PERF" in LOG: self.log.reduce_volume.append(volume)
    def push(self, token):
        if "DEBUG" in LOG:
            print("Push:")
            print("\tToken:", token)
            print()
            nonterminals = []
            edge = self.edge
            while edge:
                edge_re = []
                for match in edge:
                    if match.pos:
                        continue
                    symbol = match.rule.symbol
                    if symbol not in nonterminals:
                        nonterminals.append(symbol)
                        edge_re.extend(match.parents)
                edge = edge_re
            print("\tNonterminals starting now:")
            if nonterminals:
                print("\t\t" + " ".join(reversed(nonterminals)))

            # NOTE: need to cache here, WS_item -> EOL/ENTER/LEAVE push the same rules 3 times a couple layers above them

            terminals = set()
            for match in self.edge:
                terminals.add(match.rule.pattern[match.pos].name)
            print("\tExpected terminals:")
            if terminals:
                print("\t\t" + " ".join(sorted(sorted(terminals, key=str.lower), key=len, reverse=True)))
            print()
            # the limit - 80 chars

        if "PERF" in LOG:
            self.log.edge.append(len(self.edge))

            nodes = set(self.edge)
            edge = self.edge
            while edge:
                edge_re = []
                for match in edge:
                    for parent in match.parents:
                        if parent not in nodes:
                            nodes.add(parent)
                            edge_re.append(parent)
                edge = edge_re
            self.log.tree_size.append(len(nodes))

            import time
            start = time.time()

        edge = []
        if "DEBUG" in LOG:
            print("\tPushed:")
            pushed = []
        for match in self.edge:
            rule = match.rule
            symbol = rule.pattern[match.pos]
            if symbol.name == token.type:
                if "DEBUG" in LOG:
                    pushed.append("[{}] in   ".format(match.pos) + str(match.rule))
                Parser.add_child(rule, match.node, match.pos, Parser.create_terminal(token.type, getattr(token, "data", None)))
                match.pos += symbol.next
                edge.append(match)
        if "DEBUG" in LOG:
            for desc in pushed:
                print("\t\t" + desc)
            print()
        self.edge = edge
        self.reduce()
        if "PERF" in LOG:
            self.log.time.append(time.time() - start)
    def parse(self, lexer, symbol=None):
        self.init_search(symbol)
        for token in lexer:
            self.push(token)
            if not self.possible():
                return
    class PatternContext:
        def __init__(self, parser, pattern):
            self.parser = parser
            symbol = utils.hex(cond=lambda id: id not in self.parser.symbol_rules)
            self.rule = twocode.parser.Grammar.Rule(symbol, pattern)
        def __enter__(self):
            self.parser.symbol_rules[self.rule.symbol] = [self.rule]
            self.parser.init_search(self.rule.symbol)
            return self
        def __exit__(self, type, value, traceback):
            del self.parser.symbol_rules[self.rule.symbol]
    def pattern_context(self, *pattern):
        return Parser.PatternContext(self, pattern)
    def possible(self):
        return len(self.edge) > 0
    def copy(self):
        parser = Parser(self.rules)
        parser.edge = copy.deepcopy(self.edge)
        return parser

class Rule:
    def __init__(self, symbol, pattern):
        self.symbol = symbol
        self.pattern = pattern
        self.lookup = None
        if "DEBUG" in LOG: self.name = None
    def __str__(self):
        return "{} -> {}".format(self.symbol, " ".join("{}[{},{}]".format(symbol.name, symbol.next, symbol.skip if symbol.skip is not None else "") for symbol in self.pattern))
    class Symbol:
        """
            regular     next = +1, skip = None
            optional    next = +1, skip = +1
            list create next = +1, skip = +3
            list delim  next = +1, skip = +2
            list append next = -1, skip = None
        """
        def __init__(self, name, next, skip):
            self.name = name
            self.next = next
            self.skip = skip

class Grammar:
    def __init__(self):
        self.rules = []
        self.ops = {}
        self.literals = {}
    def form_rules(self):
        self.gen_names()
        prototype_rules = [copy.deepcopy(rule) for rule in self.rules]
        self.sub_ws()
        self.add_ops()
        self.add_literals()
        rules = self.gen_mov_rules()
        self.gen_lookup(rules)
        self.node_types, self.transform = self.gen_transform(prototype_rules, self.rules, rules)
        return rules
    def sub_ws(self):
        self.add_symbol("WS_item", [
            Grammar.Rule(pattern, pattern[0], allow_ws=False) for pattern in [
                ["EOL"],
                ["ENTER"], ["LEAVE"],
            ]
        ])
        self.add_symbol("WS", [
            Grammar.Rule(["WS_item"], "create", allow_ws=False),
            Grammar.Rule(["WS", "WS_item"], "append", allow_ws=False),
        ])
        for rule in self.rules:
            if rule.symbol == "WS":
                rule.symbol = "_WS"
            for symbol in rule.pattern:
                if symbol.name == "WS":
                    symbol.name = "_WS"
        self.add_symbol("WS_item", [Grammar.Rule(["WS"])])
    def add_ops(self):
        """
            Map<Tuple<K,V>> parsed '>>' as bit shift
            build operators from characters in grammar
        """
        for symbol, group in self.ops.items():
            for item in group:
                rule = Grammar.Rule(["'" + char + "'" for char in item], symbol=symbol, allow_ws=False)
                rule.tags.add("op")
                self.rules.append(rule)
    def add_literals(self):
        S = Grammar.Symbol
        rules = [Grammar.Rule([S("LITERAL_" + literal)], literal) for literal in self.literals.keys()]
        self.add_symbol("LITERAL", rules)

    def gen_mov_rules(self):
        rules = []
        for rule in self.rules:
            pattern = []
            for pos, symbol in enumerate(rule.pattern):
                if symbol.list:
                    if symbol.list.delim:
                        group = [
                            Rule.Symbol(symbol.name, next=+1, skip=None if not symbol.opt else +3),
                            Rule.Symbol(symbol.list.delim, next=+1, skip=+2),
                            Rule.Symbol(symbol.name, next=-1, skip=None),
                        ]
                        if len(rule.pattern) > pos + 1 and rule.pattern[pos + 1].name == symbol.list.delim:
                            group[1].skip = None
                            group[2].skip = 2
                            # REASON:
                            # the delim would skip into the trailing delim, breaking the uniqueness
                            # we make it inaccessible, but we don't remove it because of transform
                            # where we walk the pattern and match it with the original
                    else:
                        group = ([Rule.Symbol(symbol.name, next=+1, skip=None)] if not symbol.opt else []) +\
                            [Rule.Symbol(symbol.name, next=0, skip=+1)]
                else:
                    group = [Rule.Symbol(symbol.name, next=+1, skip=None if not symbol.opt else +1)]
                pattern.extend(group)
            if rule.allow_ws:
                spaced_pattern = pattern.copy()
                pos_map = {}
                spaces = set()
                for i in reversed(range(len(pattern) - 1)):
                    if not (pattern[i].name == "_WS" or pattern[i + 1].name == "_WS"):
                        spaced_pattern.insert(i + 1, Rule.Symbol("_WS", next=+1, skip=+1))
                        spaces.add(i + 1)
                for pos, symbol in enumerate(pattern):
                    pos_map[pos] = spaced_pattern.index(symbol)
                pos_map[len(pattern)] = len(spaced_pattern)
                for pos, symbol in enumerate(pattern):
                    symbol.next = pos_map[pos + symbol.next] - (1 if pos + symbol.next in spaces else 0) - pos_map[pos]
                    # NOTE:
                    # move to its ws first
                    # 0 to -1, list_append inherits allow_ws
                    if symbol.skip:
                        symbol.skip = pos_map[pos + symbol.skip] - pos_map[pos]
                        # NOTE: skip directly into it
                pattern = spaced_pattern
            parser_rule = Rule(rule.symbol, pattern)
            if "DEBUG" in LOG: parser_rule.name = str(rule)
            rules.append(parser_rule)
        return rules
    def gen_lookup(self, rules):
        """
            DESIGN:
            lookup had this vision where at each position
            a single table access would move you to the next
            this works with rules made of terminals,
            but we need to know which nonterminals to split into
            and once awaiting a terminal, there's no point in any lookup
        """
        for rule in rules:
            rule.lookup = []
            for pos in range(len(rule.pattern)):
                lookup = Grammar.LookupItem()
                while True:
                    symbol = rule.pattern[pos]
                    lookup.table[symbol.name] = pos
                    if symbol.skip is None:
                        break
                    pos += symbol.skip
                    if pos == len(rule.pattern):
                        lookup.skips_out = True
                        break
                rule.lookup.append(lookup)
    class LookupItem:
        def __init__(self):
            self.table = {}
            self.skips_out = False
    def gen_names(self):
        rule_scope = set()
        for rule in self.rules:
            rule_name = str(rule)
            if rule_name in rule_scope:
                rule.name = "2"
                rule_name = utils.unique_name(str(rule), rule_scope)
                rule.name = rule_name[len(rule.symbol + "_"):]
            rule_scope.add(rule_name)
    def gen_transform(self, prototype_rules, rules, rule_copies):
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
            GenNode = twocode.utils.node.node_gen(str(rule), vars)
            return GenNode
        nonterminals = {rule.symbol for rule in prototype_rules}
        used_types = {symbol.name for rule in prototype_rules for symbol in rule.pattern if symbol.var}
        # REASON: discard types that won't be created
        copy_to_rule = {rule_copy: rule for rule, rule_copy in zip(rules, rule_copies)}
        rule_to_copy = {rule: rule_copy for rule_copy, rule in zip(rule_copies, rules)}
        node_types = {}
        node_types["literal"] = twocode.utils.node.node_gen("literal", [Var("value"), Var("type")])
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
            return node.token
        def transform_literals(rule):
            node_type = node_types["literal"]
            if rule.symbol == "LITERAL":
                literal_type = rule.name
                return lambda node: node_type(node.children[0], literal_type)
            return lambda node: node
        def transform_type(rule):
            rule_name = str(rule)
            if rule_name not in node_types:
                return lambda node: node
            node_type = node_types[rule_name]

            assign = {}
            assign_lists = {}
            rule_copy = rule_to_copy[rule]
            names = [symbol.name for symbol in rule_copy.pattern]
            pos = -1
            for symbol in rule.pattern:
                pos = names.index(symbol.name, pos + 1)
                if symbol.var:
                    if not symbol.list:
                        assign[pos] = symbol.var
                    else:
                        assign_lists[pos] = symbol.var
                        if symbol.list.delim or not symbol.opt:
                            pos = names.index(symbol.name, pos + 1)
                            assign_lists[pos] = symbol.var

            def f(node):
                scope = {}
                for pos, child in zip(node.children_pos, node.children):
                    if pos in assign:
                        scope[assign[pos]] = child
                    if pos in assign_lists:
                        scope.setdefault(assign_lists[pos], []).append(child)
                return node_type(**scope)
            return f

        token_transform = map(leave=switch({rule: transform_op(rule) for rule in rules},
                                lambda node: copy_to_rule.get(node.rule)))
        type_map = {rule: filter(transform_literals(rule), transform_type(rule)) for rule in rules}
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
        Var = lambda name, **kwargs: Grammar.Symbol(name, var=name, **kwargs)
        class List:
            def __init__(self, delim=None):
                self.delim = delim

def example_grammar():
    Rule = Grammar.Rule
    S = Grammar.Symbol
    Var = Grammar.Symbol.Var
    List = Grammar.Symbol.List
    grammar = Grammar()

    grammar.add_symbol("file", [
        Rule([S("file_content", list=List(delim="EOL"), var="content")]),
    ])
    grammar.add_symbol("file_content", [
        Rule([S("class", var="content")]),
    ])
    grammar.add_symbol("class", [
        Rule(["'class'", S("ID", var="name"), "ENTER", S("class_content", list=List(delim="EOL"), var="content"), "LEAVE"]),
    ])
    grammar.add_symbol("class_content", [
        Rule([Var("decl")]),
        Rule([Var("func")]),
    ])
    grammar.add_symbol("line", [
        Rule([Var("expr")], "expr"),
        Rule([Var("term"), S("ASSIGN", var="op"), Var("expr")], "assign"),
        Rule([Var("decl"), "'='", Var("expr")], "def"),
        Rule([Var("decl")], "decl"),
        Rule(["'return'"], "return"),
        Rule(["'return'", Var("expr")], "returnexpr"),
    ])
    grammar.add_symbol("decl", [
        Rule([Var("type"), S("ID", var="id")]),
    ])
    grammar.add_symbol("type", [
        Rule([S("ID", var="id")], "simple"),
        Rule([S("ID", var="id"), "'<'", S("type", var="template"), "'>'"], "template"),
    ])
    grammar.add_symbol("func", [
        Rule([Var("type"), S("ID", var="id"), "'('", S("decl", list=List(delim="','"), opt=True, var="arg_list"), "')'",
              "ENTER", S("line", list=List(delim="EOL"), var="code"), "LEAVE"]),
    ])
    grammar.add_symbol("expr", [
        Rule([Var("term")], "term"),
        Rule([S("expr", var="expr1"), S("MATH", var="op"), S("expr", var="expr2")], "math"),
        Rule([S("expr", var="expr1"), S("COMPARE", var="op"), S("expr", var="expr2")], "compare"),
        Rule([S("UNARY", var="op"), Var("term")], "unary"),
        Rule([S("FIX", var="op"), Var("term")], "prefix"),
        Rule([Var("term"), S("FIX", var="op")], "postfix"),
    ])
    grammar.add_symbol("term", [
        Rule([S("ID", var="id")], "id"),
        Rule([S("LITERAL", var="literal")], "literal"),
        Rule([Var("term"), "'('", S("expr", list=List(delim="','"), opt=True, var="expr_list"), "')'"], "call"),
        Rule([Var("term"), "'['", S("expr", list=List(delim="','"), opt=True, var="expr_list"), "']'"], "index"),
        Rule([Var("term"), "'.'", S("ID", var="id")], "access"),
        Rule(["'('", Var("expr", list=List(delim="','"), opt=True), "')'"], "parens"),
        Rule(["'['", S("expr", list=List(delim="','"), opt=True, var="expr_list"), "']'"], "array"),
    ])

    return grammar

if __name__ == "__main__":
    import twocode.parser.lexer
    lex_lang = twocode.parser.lexer.example_lex()
    lex_model = lex_lang.form_model()
    lexer = lex_model.form_lexer()

    grammar = example_grammar()
    grammar.ops = lex_lang.ops
    grammar.literals = lex_lang.literals
    rules = grammar.form_rules()
    parser = Parser(rules)
    with open("samples/test.txt") as file:
        import time
        start = time.time()

        parser.parse(lexer.parse(file.read()))
        ast = parser.match()
        ast = grammar.transform(ast)
        print(ast)

        delta = time.time() - start
        print("finished in {:.2f} seconds".format(delta))

        def print_tree(node):
            def travel(node):
                type_name = type(node).__name__
                if len(node.children) == 1:
                    lines = travel(node.children[0])
                    lines[0] = "|___{}.{}".format(type_name, lines[0][4:])
                    # or more rich?
                    return lines
                files = []
                dir_lines = []
                for child in node.children:
                    lines = travel(child)
                    if len(lines) == 1:
                        files.append(lines[0][4:])
                    else:
                        for line in lines:
                            lines.append("| " + line)
                file_lines = [] # it would have to know how deep it is?
                # minimum 40 chars from the left
                # :
                return ["|____" + type_name] + dir_lines
            return "\n".join(travel(node))
        print()
        print(print_tree(ast))

        # all children which don't have children
        # pack together, first, join by ", " to 80 chars max

        # |____Event, Log, Relay

# match deepcopy
# push 80 chars
# push comment

# [2]map x 3 # 30x map
    # or just shared?
    # remove the printing and debug when done
# comments
