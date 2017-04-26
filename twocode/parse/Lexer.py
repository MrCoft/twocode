import re
from twocode.utils.Nodes import all_common, free_batch, substr
from twocode.utils.Interface import preview
from twocode.utils.String import shared_str

# ignore ws linesf

class Token:
    def __init__(self):
        self.type = None
    def __repr__(self):
        return str(self.__dict__)

class Lexer:
    def __init__(self):
        self.rules = []
        self.buffer = ""
        self.tokens = []
    current = None
    def parse(self, buffer):
        self.buffer = buffer
        self.tokens = []
        def match():
            for rule in self.rules:
                if rule(self):
                    return True
            return False
        Lexer.current = self
        while self.buffer:
            while not self.tokens:
                if not match():
                    raise Lexer.NoMatch()
            for token in self.tokens:
                yield token
            self.tokens.clear()
    class NoMatch(Exception):
        pass
# not truly incremental

#class SourceStream:
    # tags tokens

# incremental
# plug in another stream, generator, or stdin

# comparison
    # survive indent unput
    # buffer length
    # skip var











class LexModel:
    def __init__(self):
        self.patterns = []
        self.actions = []
        self.tokens = []
    def form_lexer(self):
        lexer = Lexer()
        line = 1
        indent_stack, last_indent = [], ""
        lexer.filename = "<stdin>"
        def push(type, data=None):
            token = Token()
            token.type = type
            if data:
                token.data = data
            # token.source = LexModel.Source(lexer.filename, line) # clear source architecture
            # line, indent are just lost, attaching filename to the lexer is awful
            lexer.tokens.append(token)
        def rule_gen(pattern, action, token):
            pattern = re.compile(pattern)
            def basic_rule_gen(f):
                def rule(lexer):
                    result = pattern.match(lexer.buffer)
                    if result:
                        match = result.group()
                        lexer.buffer = lexer.buffer[len(match):]
                        push(*f(match))
                    return bool(result)
                return rule
            rule_pass = basic_rule_gen(lambda match: (token, match))
            rule_token = basic_rule_gen(lambda match: (token, None))
            rule_raw = basic_rule_gen(lambda match: ("'" + match + "'", match))
            def rule_none(lexer):
                result = pattern.match(lexer.buffer)
                if result:
                    match = result.group()
                    lexer.buffer = lexer.buffer[len(match):]
                return bool(result)
            def rule_indent(lexer):
                result = pattern.match(lexer.buffer)
                if result:
                    match = result.group()
                    nonlocal line, last_indent
                    line += 1
                    lexer.buffer = lexer.buffer[len(match)-1:]
                    ws = match[:-1].lstrip("\r\n")
                    last_len = len(last_indent)
                    dedent = 0
                    if not ws.startswith(last_indent):
                        shared_len = shared_str(ws, last_indent)
                        while last_len > shared_len:
                            last_len -= indent_stack.pop()
                            dedent += 1
                            push("LEAVE")
                    indent = ws[last_len:]
                    push("EOL")
                    if indent:
                        indent_stack.append(len(indent))
                        push("ENTER", indent)
                    last_indent = ws
                return bool(result)
            def line_f(match):
                nonlocal line
                line += 1
                return "EOL", None
            rule_line = basic_rule_gen(line_f)
            def error_f(match):
                nonlocal line
                raise Lexer.NoMatch("no match for '{}'\n".format(match)
                    + preview(" @ {}: {}".format(line, repr(match + Lexer.current.buffer))))
            rule_error = basic_rule_gen(error_f)
            rule = locals()["rule_" + action]
            return rule
        for pattern, action, token in zip(self.patterns, self.actions, self.tokens):
            lexer.rules += [rule_gen(pattern, action, token)]
        parse_f = lexer.parse
        def wrap_parse(*args, **kwargs):
            for token in parse_f(*args, **kwargs):
                yield token
            nonlocal indent_stack, last_indent
            for indent_len in indent_stack:
                token = Token()
                token.type = "LEAVE"
                yield token
            indent_stack, last_indent = [], ""
        lexer.parse = wrap_parse
        return lexer
    def add_rule(self, pattern, action="pass", token=None):
        self.patterns.append(pattern)
        self.actions.append(action)
        self.tokens.append(token)
    class Source:
        def __init__(self, file, line, col, length):
            self.file = file
            self.line = line
            self.col = col
            self.length = length
        def __str__(self):
            return "{}:{}: characters {}-{}".format(self.file, self.line, self.col, self.col + self.length)

class LexLanguage:
    def __init__(self):
        self.keywords = set()
        self.ops = {}
        self.raw = set()
        self.literals = {}
        self.allow_ws = False
        self.indent_block = False

        self.unfit = {}
    def form_model(self):
        lex_model = LexModel()
        all, common = all_common(self.ops.values())
        common |= all & self.raw
        all -= self.raw
        for name, group in self.ops.items():
            match = group & common
            if match:
                self.unfit[name] = match
        sort = lambda list: sorted(sorted(list), key=len)
        all = all.union(self.raw)
        for batch in free_batch(list(all), substr):
            all -= set(batch)
            for name, group in self.ops.items():
                items = set()
                for item in group:
                    if item in batch and item not in common:
                        items.add(item)
                        batch.remove(item)
                if items:
                    lex_model.add_rule("|".join(re.escape(item) for item in sort(items)), "pass", name)
            if batch:
                lex_model.add_rule("|".join(re.escape(item) for item in sort(batch)), "raw")
        for keyword in sort(self.keywords):
            lex_model.add_rule(keyword + "(?![_a-zA-Z0-9])", "raw")
        for name, literal in sort(self.literals.items()):
            lex_model.add_rule(literal, "pass", "LITERAL_" + name)
        lex_model.add_rule('[_a-zA-Z][_a-zA-Z0-9]*', "pass", "ID")
        if self.indent_block:
            lex_model.add_rule(r'(\r\n|\r|\n)[\t ]*.', "indent")
        lex_model.add_rule(r'\r\n|\r|\n', "line")
        lex_model.add_rule(r'[ \t]+', "token" if self.allow_ws else "none", "WS")
        lex_model.add_rule(r'.|\n', "error")
        return lex_model

def default_lex():
    lex_lang = LexLanguage()
    lex_lang.keywords = {"if", "while", "for", "class", "return"}
    lex_lang.ops = {
        "ASSIGN": {'+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '>>>=', '&&=', '||=', '='},
        "COMPARE": {'<', '>', '<=', '>=', '!=', '=='},
        "MATH": {'+', '-', '*', '/', '%', '&', '|', '^', '<<', '>>', '>>>', '&&', '||'},
        "FIX": {'++', '--'},
        "UNARY": {'+', '-', '!', '~'}
    }
    lex_lang.raw = {'=', '(', ')', '[', ']', '{', '}', '.', ',', '<', '>'}
    lex_lang.literals = {
        "boolean": 'true|false',
        "integer": '0|[1-9][0-9]*',
        "hexadecimal": '0[xX][0-9a-fA-F]+',
        "octal": '0[0-7]+',
        "binary": '0[bB][01]+',
        "string": r'\"((\\\")*[^\"\r\n]?)*\"'
    }
    lex_lang.allow_ws = True
    lex_lang.indent_block = True
    return lex_lang

if __name__ == "__main__":
    lex_lang = default_lex()
    lex_model = lex_lang.form_model()
    print("unfit:", lex_lang.unfit)
    lexer = lex_model.form_lexer()
    with open("samples/test.txt") as file:
        try:
            for token in lexer.parse(file.read()):
                print(token)
        except Lexer.NoMatch as error:
            print(error)