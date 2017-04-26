import pprint
from twocode import Utils
from twocode.utils.Nodes import Node
import twocode.parse.Grammar
import copy

class Parser:
    def __init__(self, rules):
        '''
            applicable - rules by their last symbol
        '''
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
    current = None
    def parse(self, lexer):
        self.buffer = []
        self.trees = []
        Parser.current = self
        for token in lexer:
            self.buffer.append(token)
            tree = Parser.Tree(token.type)
            self.trees.append(tree)
            while tree.edge:
                tree.expand()
    def match(self, symbol=None):
        if symbol is None: symbol = self.rules[0].symbol
        if symbol in self.trees[-1].reduces:
            if len(self.buffer) in self.trees[-1].reduces[symbol]:
                return self.first_tree(symbol, len(self.buffer) - 1, len(self.buffer))
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
    class Tree:
        ''' submatches at a position '''
        def __init__(self, symbol):
            '''
                reduces - complete parsed subtrees
                    {expr: {len: [(rule_call, [1,13,4]),..
                    for each symbol, length, rule, distribution
                edge - unexpanded lengths for each symbol at current position
            '''
            self.reduces = {symbol: {1: [(None, [1])]}}
            self.edge = {symbol: {1}}
        def expand(self):
            parser = Parser.current
            edge = {}
            for last_symbol, lens in self.edge.items():
                rules = parser.applicable[last_symbol]
                for rule in rules:
                    for symbol_len in lens:
                        def pattern_distribs(pattern_index, at):
                            '''
                                goes backwards through a rule's pattern, gathering distributions
                                by going through possible symbol lengths and stepping back through the trees
                            '''
                            if at >= 0:
                                tree = parser.trees[at]
                                symbol = rule.pattern[pattern_index]
                                if symbol in tree.reduces:
                                    lens = sorted(tree.reduces[symbol].keys())
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
                            distribs = pattern_distribs(len(rule.pattern) - 2, len(parser.trees) - 1 - symbol_len)
                        else:
                            distribs = [[]]
                        if distribs:
                            symbol = rule.symbol
                            self.reduces.setdefault(symbol, {})
                            for distr in distribs:
                                distr += [symbol_len]
                                match_len = sum(distr)
                                if not self.reduces[symbol].setdefault(match_len, []):
                                    edge.setdefault(symbol, set()).add(match_len)
                                self.reduces[symbol][match_len].append((rule, distr))
            self.edge = edge
    def first_tree(self, symbol, at, symbol_len):
        rule, distr = self.trees[at].reduces[symbol][symbol_len][0]
        if not rule:
            return Node(rule=None, token=self.buffer[at])
        jump = at - symbol_len
        children = []
        for sym, sym_len in zip(rule.pattern, distr):
            jump += sym_len
            children.append(self.first_tree(sym, jump, sym_len))
        return Node(rule=rule, children=children)
    def enum_trees(self, symbol, at, symbol_len):
        '''
            builds a symbol, combining possible distributions
        '''
        trees = []
        for rule, distr in self.trees[at].reduces[symbol][symbol_len]:
            if not rule:
                trees += [Node(rule=None, token=self.buffer[at])]
                continue
            branches = None
            jump = at - symbol_len
            for sym, sym_len in zip(rule.pattern, distr):
                jump += sym_len
                sym_trees = self.enum_trees(sym, jump, sym_len)
                if not branches:
                    branches = [Node(rule=rule, children=[tree]) for tree in sym_trees]
                else:
                    branches = [Node(rule=tree.rule, children=tree.children + [subtree]) for tree in branches for
                                subtree in sym_trees]
            trees += branches
        return trees
    def __str__(self):
        return pprint.pformat(self.rules)

class IncrementalParser:
    def __init__(self, rules):
        self.rules = rules
        self.symbol_rules = {}
        for rule in self.rules:
            self.symbol_rules.setdefault(rule.symbol, []).append(rule)
    def init_search(self, symbol=None):
        if symbol is None: symbol = self.rules[0].symbol
        self.edge = [IncrementalParser.Branch(None, rule) for rule in self.symbol_rules[symbol]]
        self.expand()
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
    class Branch:
        def __init__(self, parents, rule):
            self.parents = parents
            self.rule = rule
            self.children = []
        def __deepcopy__(self, memo):
            branch = IncrementalParser.Branch(copy.deepcopy(self.parents, memo=memo), self.rule)
            copy_node = lambda node: Node(rule=node.rule, children=[copy_node(child) for child in node.children], **Utils.redict(node.__dict__, "rule children".split()))
            branch.children = [copy_node(child) for child in self.children]
            return branch
    def expand(self):
        edge = self.edge
        self.edge = []
        self.matches = []
        while edge:
            edge_re = []
            for branch in edge:
                if len(branch.children) == len(branch.rule.pattern):
                    if not branch.parents:
                        self.matches.append(Node(rule=branch.rule, children=branch.children))
                    else:
                        for parent in branch.parents:
                            parent_branch = IncrementalParser.Branch(parent.parents, parent.rule)
                            parent_branch.children = list(parent.children)
                            parent_branch.children.append(Node(rule=branch.rule, children=branch.children))
                            edge_re.append(parent_branch)
                else:
                    self.edge.append(branch)
            edge = edge_re
        edge = self.edge
        self.edge = []
        shared_gen = {}
        while edge:
            edge_re = []
            for branch in edge:
                symbol = branch.rule.pattern[len(branch.children)]
                if symbol in self.symbol_rules:
                    for rule in self.symbol_rules[symbol]:
                        if rule not in shared_gen:
                            shared_gen[rule] = IncrementalParser.Branch([], rule)
                            edge_re.append(shared_gen[rule])
                        shared_gen[rule].parents.append(branch)
                else:
                    self.edge.append(branch)
            edge = edge_re
    def push(self, token):
        edge = []
        for branch in self.edge:
            rule = branch.rule
            if rule.pattern[len(branch.children)] == token.type:
                branch.children.append(Node(rule=None, token=token))
                edge.append(branch)
        self.edge = edge
        self.expand()
    def parse(self, lexer, symbol=None):
        self.init_search(symbol)
        for token in lexer:
            self.push(token)
    class PatternContext:
        def __init__(self, parser, pattern):
            self.parser = parser
            symbol = Utils.hex_id(cond=lambda id: id not in self.parser.symbol_rules)
            self.rule = Grammar.Rule(symbol, pattern)
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
    import Lexer
    import Grammar

    lex_lang = Lexer.default_lex()
    lex_model = lex_lang.form_model()
    lexer = lex_model.form_lexer()

    grammar = Grammar.default_grammar()
    grammar.literals = lex_lang.literals
    grammar.unfit = lex_lang.unfit
    rules = grammar.form_rules()
    parser = Parser(rules)
    with open("samples/test.txt") as file:
        parser.parse(lexer.parse(file.read()))
        ast = parser.match()
        ast = grammar.transform(ast)
        print(ast)