def loops(rules):
    symbols = set(rule.symbol for rule in rules) | set(symbol for rule in rules for symbol in rule.pattern)
    map_to = {key: set() for key in symbols}
    for rule in rules:
        for symbol in rule.pattern:
            map_to[symbol].add(rule.symbol)

    changed = True
    while changed:
        changed = False
        for from_symbol in symbols:
            from_map = map_to[from_symbol]
            for symbol in from_map.copy():
                for to_symbol in map_to[symbol]:
                    if to_symbol not in from_map:
                        from_map.add(to_symbol)
                        changed = True

    return [rule for rule in rules if set.intersection(map_to[rule.symbol], rule.pattern)]

def form_prec(pattern, ops=None, symbol=None, assoc="left"):
    return [(pattern, ops, symbol, assoc)]

def pattern_match(pattern, rule):
    index = 0
    try:
        for symbol in pattern.split():
            index = rule.pattern.index(symbol, index)
    except ValueError:
        return False
    return True
#         symbol=non-null - talks about specific characters

# parens, code
# written in that it can kill partial result in the incremental
def gen_valid_prec(rules, prec):
    def gen(layer):
        return lambda node: layer
    def gen_math(rule, symbol):
        index = rule.pattern.index(symbol)
        def node_layer(node):
            op = node.children[index].rule.pattern[0][1:-1]
            return op_map[op]
        return node_layer

    rule_map = {}
    op_map = {}
    for layer, items in enumerate(prec):
        layer += 1
        for pattern, ops, symbol, assoc in items:
            for rule in rules:
                if not pattern_match(pattern, rule):
                    continue
                if symbol and rule.symbol != symbol:
                    continue
                if not ops:
                    rule_map[rule] = gen(layer)
                else:
                    for op in ops.split():
                        op_map[op] = layer
                    rule_map[rule] = gen_math(rule, pattern)

    def node_layer(node):
        #if node.rule in parens:
        #    return 0
        if not node.children:
            return 0
        children = [node_layer(child) for child in node.children]
        exprs_layer = max(children)
        if node.rule not in rule_map:
            return exprs_layer
        layer = rule_map[node.rule](node)
        if exprs_layer > layer:
            raise SyntaxError("wrong operator precedence in AST")
        return layer
    return node_layer

if __name__ == "__main__":
    import twocode.parser.lexer
    lex_lang = twocode.parser.lexer.default_lex()
    lex_model = lex_lang.form_model()
    lexer = lex_model.form_lexer()

    import twocode.parser.grammar
    grammar = twocode.parser.grammar.default_grammar()
    grammar.literals = lex_lang.literals
    grammar.unfit = lex_lang.unfit
    rules = grammar.form_rules()
    from . import IncrementalParser
    parser = Parser.IncrementalParser(rules)
    with open("samples/test.txt") as file:
        parser.parse(lexer.parse(file.read()))

    rules = loops(rules)
    for rule in rules:
        print(rule)
    print(len(parser.matches), "parses")

    P = form_prec

    rule_map = {}
    prec = [
        P("* +", "_MATH"),
        P("<<", "_MATH"),
        P("%", "_MATH"),
    ]
    valid_prec = gen_valid_prec(rules, prec)
    matches = []
    for ast in parser.matches:
        try:
            valid_prec(ast)
            matches.append(ast)
        except SyntaxError:
            pass
    print(len(matches), "valid parses")

# precedence to grammar alteration?
