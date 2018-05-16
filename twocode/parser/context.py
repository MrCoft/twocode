class Context:
    def __init__(self, lex_lang, grammar):
        self.lex_lang = lex_lang
        self.grammar = grammar
        lex_model = lex_lang.form_model()
        self.lexer = lex_model.form_lexer()

        grammar.ops = lex_lang.ops
        grammar.literals = lex_lang.literals
        self.rules = grammar.form_rules()
        self.parser = None

        self.node_types = grammar.node_types
        self.transforms = [grammar.transform]

    def parse(self, code):
        self.parser.parse(self.lexer.parse(code))
        ast = self.parser.match()
        return self.transform(ast)
    def transform(self, ast):
        if ast is None: return None
        for transform in self.transforms:
            ast = transform(ast)
        return ast
