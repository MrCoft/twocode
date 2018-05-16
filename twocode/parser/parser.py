import pprint
from twocode import utils
from twocode.utils.node import Node
import twocode.parser.grammar
import copy

LOG = set()
#LOG.add("PERF")

class Parser:
    def __init__(self, rules):
        """
            DESIGN:
            finds ways to build symbols out of symbols for every position in the buffer
            uses a convention of searching by rule's pattern's last symbol
            and stores end positions of submatches

            say you want to build C -> A B at 100
            100 says you can build 10 and 15 length B that end there
            you look for A at 90 and 85, find 1-length As there
            log that you can build 11 and 16 length C at 100

            VARS:
            applicable - rules by their last symbol
        """
        self.rules = rules
        symbol_scope = set(symbol for rule in self.rules for symbol in rule.pattern) | set(
            rule.symbol for rule in self.rules)
        self.applicable = {symbol: [] for symbol in symbol_scope}
        for rule in self.rules:
            self.applicable[rule.pattern[-1]].append(rule)
        self.symbols = []
        for rule in self.rules:
            if rule.symbol not in self.symbols:
                self.symbols.append(rule.symbol)
    def parse(self, lexer):
        """
            push sequentially, at each position building from those before
            a complete match will have a buffer-length "file" symbol built at the last position
        """
        self.buffer = []
        self.submatches = []
        for token in lexer:
            self.push(token)
    def push(self, token):
        """
            start with the raw token then reduce repeatedly
            reduce checks if any rule can build anything new   # there's no expand/reduce
            "edge" being the most recently added submatches

            VARS:
            reduces - complete parsed submatches at a position
                {expr: {len: [(rule_call, [1, 13, 4]),..
                for each symbol, length, rule, distribution
            edge - unreduced lengths for each symbol at current position
        """
        self.buffer.append(token)
        symbol = token.type
        reduces = {symbol: {1: [(None, [1])]}}
        self.submatches.append(reduces)
        edge = {symbol: {1}}
        while edge:
            edge_re = {}
            for last_symbol, lens in edge.items():
                rules = self.applicable[last_symbol]
                for rule in rules:
                    for symbol_len in lens:
                        def pattern_distribs(pattern_index, at):
                            """
                                goes backwards through a rule's pattern, gathering distributions
                                by going through possible symbol lengths and stepping back through the submatches
                            """
                            if at >= 0:
                                submatch = self.submatches[at]
                                symbol = rule.pattern[pattern_index]
                                if symbol in submatch:
                                    lens = sorted(submatch[symbol].keys())
                                else:
                                    return []
                                if pattern_index == 0:
                                    distribs = []
                                    for symbol_len in lens:
                                        distribs.append([symbol_len])
                                else:
                                    distribs = []
                                    for symbol_len in lens:
                                        for distr in pattern_distribs(pattern_index - 1, at - symbol_len):
                                            distribs.append(distr + [symbol_len])
                                return distribs
                            else:
                                return []
                        if len(rule.pattern) > 1:
                            distribs = pattern_distribs(len(rule.pattern) - 2, len(self.submatches) - 1 - symbol_len)
                        else:
                            distribs = [[]]
                        if distribs:
                            symbol = rule.symbol
                            reduces.setdefault(symbol, {})
                            for distr in distribs:
                                distr += [symbol_len]
                                match_len = sum(distr)
                                if not reduces[symbol].setdefault(match_len, []):
                                    edge_re.setdefault(symbol, set()).add(match_len)
                                reduces[symbol][match_len].append((rule, distr))
            edge = edge_re
    def match(self, symbol=None):
        if symbol is None: symbol = self.rules[0].symbol
        if symbol in self.submatches[-1]:
            if len(self.buffer) in self.submatches[-1][symbol]:
                return self.first_match(symbol, len(self.buffer) - 1, len(self.buffer))
        raise Parser.NoMatch(symbol)
    def best_match(self):
        for symbol in self.symbols:
            try:
                return self.match(symbol)
            except Parser.NoMatch:
                pass
        raise Parser.NoMatch("symbol")
    class NoMatch(Exception):
        pass
    def first_match(self, symbol, at, symbol_len):
        rule, distr = self.submatches[at][symbol][symbol_len][0]
        if not rule:
            return Node(rule=None, token=getattr(self.buffer[at], "data", None))
        jump = at - symbol_len
        children = []
        for sym, sym_len in zip(rule.pattern, distr):
            jump += sym_len
            children.append(self.first_match(sym, jump, sym_len))
        return Node(rule=rule, children=children)
    def enum_matches(self, symbol, at, symbol_len):
        """
            builds a symbol, combining possible distributions
        """
        matches = []
        for rule, distr in self.submatches[at][symbol][symbol_len]:
            if not rule:
                matches += [Node(rule=None, token=getattr(self.buffer[at], "data", None))]
                continue
            submatches = None
            jump = at - symbol_len
            for sym, sym_len in zip(rule.pattern, distr):
                jump += sym_len
                sym_matches = self.enum_matches(sym, jump, sym_len)
                if not submatches:
                    submatches = [Node(rule=rule, children=[sym_match]) for sym_match in sym_matches]
                else:
                    re = []
                    for submatch in submatches:
                        for sym_match in sym_matches:
                            node = copy.deepcopy(submatch)
                            node.children.append(copy.deepcopy(sym_match))
                            re.append(node)
                    submatches = re
                    # NOTE: matches can't share submatch instances, it breaks transform
            matches += submatches
        return matches
    def __str__(self):
        return pprint.pformat(self.rules)

class IncrementalParser:
    """
        DESIGN:
        built to be fed tokens, can tell you when exactly matching becomes impossible
        useful for manual grammar for preprocessors

        you start with init_search() for a symbol
        IP expands that into more symbols, looking through all possible ways each symbol can be created
        creating a graph of incomplete nodes with those expecting raw tokens being the edge
        you can get to the same symbol by different paths
        so we merge them, creating nodes with multiple parents

        on push, feed the token into nodes expecting it and discard the rest
        if this was the last token the node needed it creates a copy of its parent and inserts itself into it
        looks what is needed next, expands into new edge nodes
        when this propagates to the required symbol, a full match is found
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
            )
    def init_search(self, symbol=None):
        if symbol is None: symbol = self.rules[0].symbol
        self.edge = [IncrementalParser.Match([], rule) for rule in self.symbol_rules[symbol]]
        self.reduce()
        self.matches = []
        if "PERF" in LOG: self.log.reduce_volume.pop()
    def match(self):
        if self.matches:
            return self.matches[0]
        elif self.possible():
            return None
        else:
            raise IncrementalParser.NoMatch()
    class NoMatch(Exception):
        def __str__(self):
            return "match not possible"
    class Match:
        def __init__(self, parents, rule):
            self.parents = parents
            self.rule = rule
            self.children = []
        def __deepcopy__(self, memo):
            match = IncrementalParser.Match(copy.deepcopy(self.parents, memo=memo), self.rule)
            copy_node = lambda node: Node(rule=node.rule, children=[copy_node(child) for child in node.children], **utils.redict(node.__dict__, "rule children".split()))
            match.children = [copy_node(child) for child in self.children]
            return match
    def reduce(self):
        if "PERF" in LOG: volume = 0
        edge = self.edge
        self.edge = []
        self.matches = []
        while edge:
            if "PERF" in LOG: volume += len(edge)
            edge_re = []
            for match in edge:
                if len(match.children) == len(match.rule.pattern):
                    if not match.parents:
                        self.matches.append(Node(rule=match.rule, children=match.children))
                    else:
                        for parent in match.parents:
                            parent_match = IncrementalParser.Match(parent.parents, parent.rule)
                            parent_match.children = parent.children.copy()
                            parent_match.children.append(Node(rule=match.rule, children=match.children))
                            edge_re.append(parent_match)
                else:
                    self.edge.append(match)
            edge = edge_re
        edge = self.edge
        self.edge = []
        shared_gen = {}
        while edge:
            if "PERF" in LOG: volume += len(edge)
            edge_re = []
            for match in edge:
                symbol = match.rule.pattern[len(match.children)]
                if symbol in self.symbol_rules: # to per symbol
                    for rule in self.symbol_rules[symbol]:
                        if rule not in shared_gen:
                            shared_gen[rule] = IncrementalParser.Match([], rule)
                            edge_re.append(shared_gen[rule])
                        shared_gen[rule].parents.append(match)
                else:
                    self.edge.append(match)
            edge = edge_re
        if "PERF" in LOG: self.log.reduce_volume.append(volume)
    def push(self, token):
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
        for match in self.edge:
            rule = match.rule
            if rule.pattern[len(match.children)] == token.type:
                match.children.append(Node(rule=None, token=getattr(token, "data", None)))
                edge.append(match)
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
            self.rule = twocode.parser.grammar.Rule(symbol, pattern)
        def __enter__(self):
            self.parser.symbol_rules[self.rule.symbol] = [self.rule]
            self.parser.init_search(self.rule.symbol)
            return self
        def __exit__(self, type, value, traceback):
            del self.parser.symbol_rules[self.rule.symbol]
    def pattern_context(self, *pattern):
        return IncrementalParser.PatternContext(self, pattern)
    def possible(self):
        return len(self.edge) > 0
    def copy(self):
        parser = IncrementalParser(self.rules)
        parser.edge = copy.deepcopy(self.edge)
        return parser

if __name__ == "__main__":
    import twocode.parser.lexer
    lex_lang = twocode.parser.lexer.example_lex()
    lex_model = lex_lang.form_model()
    lexer = lex_model.form_lexer()

    import twocode.parser.grammar
    grammar = twocode.parser.grammar.example_grammar()
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
        print(len(parser.enum_matches(rules[0].symbol, len(parser.buffer) - 1, len(parser.buffer))), "matches")
        """
            NOTE: replacing List() with List(delim="','"/"EOL") in the grammar reduced matches from 192 to 4
            2 are because of operator precedence in "2 + 3 << 4"
            2 are because of an empty line, EOL EOL matching two ways:
                S("line", list=List(delim="EOL"), ... allow_ws=True)
                line_list -> line_list _WS EOL line
                line_list -> line_list EOL _WS line
        """

        delta = time.time() - start
        print("finished in {:.2f} seconds".format((delta)))
