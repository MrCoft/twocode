from twocode.utils.Nodes import Node, map, l
from twocode.parse.Parser import IncrementalParser
from twocode.utils.Code import filter
from twocode.parse.Lexer import Token
import sys

# problems
# iftrue should fallback to valid content
# we dont enter into a huge block?


# tests

# if 0:
#

# for a in b:
#        0
#    olele nu

# ====

# errors as str?
# parsable by tests

# tests to objects with useful __str__

# ignore empty lines
'''
either multiple EOL to WS or dont print as error

expr_block not from WS filter
block_list
original, not {}
'''


# lexer filter func
# indent filter func
# to tests

class IndentParser:
    def __init__(self, rules):
        self.parser = IncrementalParser(rules)

        self.delims = ['EOL', ';']
        self.filter_lexer = filter(valid_indent_order, filter_lexer_fallback)
        self.filter_indent = filter(itervalid_indent_consistent, valid_indent_mixed, valid_indent_sane)
        self.filter_stmt = map(enter=filter(l(valid_inline_block)))

    def parse(self, lexer):
        buffer = list(lexer)
        errors = self.check(buffer)
        for error in errors:
            print(error, file=sys.stderr)
        self.parser.parse(buffer)
        self.matches = self.parser.matches
    def match(self):
        if self.matches:
            return self.matches[0]
        else:
            raise IndentParser.NoMatch()
    class NoMatch(Exception):
        def __str__(self):
            return "match not possible"
    def check(self, buffer, tree=None):
        if tree is None:
            tree = parse_block_tree(buffer, None)

        subtrees = tree.children
        tree_mask = [True for i in range(len(buffer))]
        for subtree in subtrees:
            for i in range(subtree.pos, subtree.pos + subtree.length):
                tree_mask[i] = False

        all_matches = [] # mb idc
        all_subs = []
        all_errors = []

        parser = self.parser
        def match():
            nonlocal parser, i, subs, matches_end, error
            end = i
            matches = []
            for match in parser.matches:
                try:
                    self.filter_stmt(match)
                except Exception as exc:
                    log_error(exc)
                    continue
                valid = end >= tree.pos + tree.length
                if not valid:
                    valid = buffer[end].type in self.delims
                if valid:
                    matches.append(match)
            if matches:
                i += 1
                print('------------------------------')
                match = matches[0]
                print(match)
                all_matches.append(match)
                all_subs.extend(subs)
                subs = []
                parser.init_search("stmt")
                matches_end = i
                if error:
                    all_errors.append(error)
                error = None
        parser.init_search("stmt")

        subs = []
        subtree = None
        def next_sub():
            nonlocal subtree
            subtree = subtrees.pop(0) if subtrees else None
        next_sub()

        matches_end = tree.pos
        error = None
        def log_error(exc=None):
            nonlocal error
            tokens = []
            for j in range(matches_end, i):
                if tree_mask[j]:
                    tokens.append(buffer[j])
            code = " ".join(str(token) for token in tokens)
            if not code:
                code = "@ {}".format(buffer[matches_end])
            if exc is None:
                exc = Exception("can't parse <stmt>")
            error = "{} from {}".format(exc, code)

        i = tree.pos
        while i < len(buffer):
            if subtree and i >= subtree.pos - 1:
                if i >= subtree.pos:
                    raise Exception("algorithm error: skipped into sub_tree")
                parser_save = parser.copy()
                print("speshul", buffer[i + subtree.length])
                parser.push(Token("'{'", '{'))
                parser.push(Token("'}'", '}'))
                # parser.push(buffer[i + subtree.length])
                if parser.matches or parser.possible():
                    subs.append(subtree)
                    i += subtree.length + 2
                    next_sub()
                    match()
                else:
                    print("tree failed")
                    for st in reversed(subtree.children):
                        subtrees.insert(0, st)
                    next_sub()
                    parser = parser_save
            else:
                print(buffer[i])
                parser.push(buffer[i])
                if parser.matches or parser.possible():
                    i += 1
                    match()
                else:
                    print("lin failed")
                    while i < len(buffer):
                        if subtree and i >= subtree.pos:
                            i += subtree.length + 1
                            next_sub()
                        elif buffer[i].type not in self.delims:
                            i += 1
                        else:
                            break
                    log_error()
                    i += 1
                    subs = []
                    parser.init_search("stmt")
                    matches_end = i
        for subtree in all_subs:
            errors = self.check(buffer, subtree)
            all_errors.extend(errors)
        return all_errors

def parse_block_tree(buffer, leave_token=None, pos=0):
    tree = Node()
    i = pos
    while i < len(buffer):
        token = buffer[i]
        if token.type == "ENTER":
            child = parse_block_tree(buffer, "LEAVE", pos=i + 1)
            i += child.length + 2
            tree.children.append(child)
        elif token.type == "{":
            child = parse_block_tree(buffer, "}", pos=i + 1)
            i += child.length + 2
            tree.children.append(child)
        elif token.type == leave_token:
            break
        elif token.type == "LEAVE":
            break
        else:
            i += 1
    tree.pos = pos
    tree.length = i - pos
    return tree

def valid_indent_order(indent):
    if indent.lstrip("\t").lstrip(" "):
        raise IndentationError()
def itervalid_indent_consistent(indents):
    style = None
    for indent in indents:
        if style is None:
            style = indent
        else:
            if indent != style:
                raise IndentationError()
def valid_indent_mixed(indent):
    if ("\t" in indent) != (" " in indent):
        raise IndentationError()
def valid_indent_sane(indent):
    if "\t" in indent:
        if len(indent) not in [1]:
            raise IndentationError()
    else:
        if len(indent) not in [1, 2, 4, 8]:
            raise IndentationError()
def filter_lexer_fallback(lexer):
    buffer = []
    error = "LEAVE EOL ENTER".split()
    for token in lexer:
        buffer.append(token.type)
        if len(buffer) > 3:
            buffer.pop(0)
        if buffer == error:
            raise IndentationError()
        yield token

def valid_inline_block(node):
    rule = node.rule
    if not rule:
        return
    symbol = node.rule.symbol
    print("symbol:", symbol)
    if symbol == "expr_block":
        pass

if __name__ == "__main__":
    from twocode.Twocode import Twocode
    twocode = Twocode()
    compiler = twocode.parser
    parser = IndentParser(compiler.parser.rules)
    parser.parse(compiler.lexer.parse(open("samples/blocky.2c").read()))