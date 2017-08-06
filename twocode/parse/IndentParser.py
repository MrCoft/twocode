from twocode.utils.Nodes import Node, range_call, l
import sys
import traceback
import textwrap

class IndentParser:
    '''
        this is designed to solve several specific problems:

        break code into scopes to isolate errors, even between statements

        not all blocks are made of code:
            a = [
                1,
            ]

        statements can be multiline if they wouldn't parse otherwise
        parse longest stmt, then find if it breaks into valid parts
        (shortest stmt parse followed by a delim fails on if-else)
            x = 1
            + 2
            y = 1 +
              2; 3
        stmts can be broken only if they are concatenated using math
        in that case, an error and a reset would lead to the error again
        so unintuitively, we do not reset the pointer

        debatable cases:
        subtree filter does not invalidate ws blocks
        valid parses may be overwritten by longer invalid parses
    '''
    def __init__(self):
        self.parser = None
        self.valid = None
        pass # other nones?
    def parse(self, lexer):
        buffer = list(lexer)
        self.parser.init_search()
        # REASON: breaks if inner parser becomes dirty
        self.num_parses = 1
        lines, self.errors = self.check(buffer)
        self.matches = [self.wrap_code(lines)]
    def match(self):
        if self.errors:
            raise Exception("\n".join([""] + [str(error) for error in self.errors]))
        return self.matches[0]
    def check(self, buffer, tree=None):
        if tree is None:
            tree = parse_block_tree(buffer)

        stmt_symbol = "stmt"
        delims = ['EOL', "';'"]
        ws = "WS EOL ENTER LEAVE".split()

        all_matches = []
        all_errors = []

        def pack_matches():
            nonlocal matches, i

            matches_re = []
            msg = None
            for match in matches:
                try:
                    self.valid(match)
                    matches_re.append(match)
                except:
                    exc_class, exc, tb = sys.exc_info()
                    msg = traceback.format_exception(exc_class, exc, None)
                    msg = "".join(msg)
            matches = matches_re
            if not matches:
                code = " ".join(str(buffer[j]) for j in skip_subs(match_pos, match_end if msg else i, subs))
                if not msg:
                    msg = Exception("can't parse <stmt>")
                error = "{}at: {}".format(msg, code)
                all_errors.append(error)
                return

            sub_pos = list(skip_subs(match_pos, match_end, subs))
            sub_buffer = [buffer[j] for j in sub_pos]
            sb_len = len(sub_buffer)

            remain_match, remain_parses = matches[0], 1
            pos = 0
            matches = []
            offsets = []
            parser.init_search(stmt_symbol)
            for i1 in range(sb_len):
                parser.push(sub_buffer[i1])
                if not (i1 + 1 >= sb_len or sub_buffer[i1 + 1] in delims):
                    continue

                matches1 = []
                for match1 in parser.matches:
                    try:
                        self.valid(match1)
                        matches1.append(match1)
                    except:
                        continue
                if not matches1:
                    continue

                i2 = i1 + 2
                while i2 < sb_len and sub_buffer[i2].type in ws:
                    i2 += 1
                parser2 = self.parser.copy()
                parser2.init_search(stmt_symbol)
                pos2 = i2
                for i2 in range(i2, i1):
                    parser2.push(sub_buffer[i2])

                matches2 = []
                for match2 in parser2.matches:
                    try:
                        self.valid(match2)
                        matches2.append(match2)
                    except:
                        continue
                for match2 in matches2:
                    matches.append(match1)
                    offsets.append(sub_pos[pos])
                    self.num_parses *= len(matches1)
                    pos = pos2
                    remain_match, remain_parses = match2, len(matches2)
                    parser.init_search(stmt_symbol)
            matches.append(remain_match)
            offsets.append(sub_pos[pos])
            self.num_parses *= remain_parses
            offsets.append(sub_pos[-1] + 2)

            all_lines = []
            for subtree in subs:
                lines, errors = self.check(buffer, subtree)
                all_lines.append(lines)
                all_errors.extend(errors)

            matches_re = []
            for match, pos, end in zip(matches, offsets[:-1], offsets[1:]):
                length = end - pos - 1
                for subtree, lines in reversed(list(zip(subs, all_lines))):
                    if pos <= subtree.pos - 1 and subtree.pos + subtree.length <= pos + length:
                        offset = subtree.pos
                        for subtree in reversed(subs):
                            if offset > subtree.pos:
                                offset -= subtree.length
                        self.insert(match, offset - pos, lines)
                matches_re.append(match)
            all_matches.extend(matches_re)

        subtrees = tree.children
        subs = []
        subtree = None
        def next_sub():
            nonlocal subtree
            subtree = subtrees.pop(0) if subtrees else None
        next_sub()

        matches = []
        match_pos, match_end = tree.pos, None
        def match():
            nonlocal matches, match_end
            if bool(parser.matches) and (i >= tree_end or buffer[i].type in delims):
                matches = parser.matches
                match_end = i

        def skip_ws():
            nonlocal i
            while i < tree_end and (buffer[i].type in ws or buffer[i].type in delims):
                i += 1

        parser = self.parser.copy()
        parser.init_search(stmt_symbol)
        i = tree.pos
        tree_end = tree.pos + tree.length
        skip_ws()
        while i < tree_end:
            if subtree and i >= subtree.pos - 1:
                if i >= subtree.pos:
                    raise Exception("algorithm error: skipped into subtree")
                blocks = [branch for branch in parser.edge if branch.rule.symbol == "block_list" and not branch.children]
                if blocks:
                    parser.edge = blocks
                    parser.push(buffer[i])
                    parser.push(buffer[i + subtree.length + 1])

                    subs.append(subtree)
                    i += subtree.length + 2
                    next_sub()
                    match()
                else:
                    for st in reversed(subtree.children):
                        subtrees.insert(0, st)
                    next_sub()
            else:
                parser.push(buffer[i])
                i += 1
                match()
                if not (parser.matches or parser.possible()):
                    pack_matches()

                    i -= 2
                    while i < tree_end:
                        if subtree:
                            if i >= subtree.pos - 2:
                                if buffer[i].type == "EOL" and buffer[i + 1].type == "ENTER":
                                    i += subtree.length + 3
                                    next_sub()
                                    continue
                            if i >= subtree.pos - 1:
                                i += subtree.length + 2
                                next_sub()
                                continue
                        if buffer[i].type in delims:
                            break
                        i += 1

                    i += 1
                    # class A: { func f(): return 2 }
                    skip_ws() # infinite loop on EOL EOL
                    matches = []
                    subs.clear()
                    parser.init_search(stmt_symbol)
                    match_pos, match_end = i, None
        pack_matches()

        return all_matches, all_errors

def parse_block_tree(buffer, leave_token=None, pos=0):
    '''
        parses into a tree of ranges, identifying nested blocks
        LEAVE has higher priority than '}' and can leave without closing some brackets
    '''
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

def skip_subs(pos, end, subtrees):
    subtrees = subtrees.copy()
    subtree = subtrees.pop(0) if subtrees else None
    i = pos
    while i < end:
        yield i
        i += 1
        if subtree and i >= subtree.pos - 1:
            yield i
            yield i + subtree.length + 1
            i += subtree.length + 2
            subtree = subtrees.pop(0) if subtrees else None

def gen_insert(rules):
    def find_type(s):
        for rule in rules:
            if repr(rule) == s:
                return lambda *args: Node(rule=rule, children=args)

    block_empty, block_list, code_append, code_stmt = [find_type(s) for s in textwrap.dedent('''
        block_list -> '{' '}'
        block_list -> '{' code '}'
        code -> code DELIM stmt
        code -> stmt
    ''').strip().splitlines()]

    def wrap_code(lines):
        if not lines:
            return block_empty()
        node = code_stmt(lines[0])
        for stmt in lines[1:]:
            node = code_append(node, Node(rule=None, token=None), stmt)
        node = block_list(Node(rule=None, token=None), node, Node(rule=None, token=None))
        # not necessary?
        return node

    def insert(node, pos, lines): # unwrap
        def insert(node, range):
            p, len = range
            rule = node.rule
            if rule and rule.symbol == "block_list":
                if p == pos - 1:
                    return wrap_code(lines)
        range_call(l(insert))(node)
    return wrap_code, insert

def gen_valid(*valids):
    def iter_tokens(node):
        for i, child in enumerate(node.children):
            if not child.rule:
                yield node, i
            else:
                for n, j in iter_tokens(child):
                    yield n, j
    def tree_call(node, f):
        for child in node.children:
            tree_call(child, f)
        f(node)
    # calls to iters

    def valid(node):
        valid_lexer_empty_line(n.rule.symbol for n, i in iter_tokens(node))
        for n, i in iter_tokens(node):
            if n.rule.symbol == "ENTER":
                indent = n.children[i].token
                valid_indent_order(indent)
        indents = []
        for n, i in iter_tokens(node):
            rule = n.rule
            if rule.symbol == "block_list" and rule.pattern[i] == "ENTER":
                indent = n.children[i].token
                indents.append(indent)
        for indent in indents:
            valid_indent_mixed(indent)
            valid_indent_odd(indent)
        itervalid_indent_consistent(indents)
        tree_call(node, valid_inline_block)
        for valid in valids:
            valid(node) #
    return valid

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
    if ("\t" in indent) == (" " in indent):
        raise IndentationError()
def valid_indent_odd(indent):
    if "\t" in indent:
        if len(indent) not in [1]:
            raise IndentationError()
    else:
        if len(indent) not in [1, 2, 3, 4, 8]:
            raise IndentationError()
def valid_lexer_empty_line(lexer):
    buffer = []
    error = "LEAVE EOL ENTER".split()
    for token in lexer:
        buffer.append(token)
        if len(buffer) > 3:
            buffer.pop(0)
        if buffer == error:
            raise IndentationError()

def valid_inline_block(node):
    rule = node.rule
    if not rule:
        return
    if rule.symbol == "expr" and "block_list" in rule.pattern:
        assert "ENTER" not in node.children[0].rule.pattern, "whitespace <expr_block>" #

'''
either isolate the ws block rule | look for block parents, we cant sub block_list
'''

if __name__ == "__main__":
    from twocode.Twocode import Twocode
    twocode = Twocode()
    compiler = twocode.parser

    parser = IndentParser()
    from twocode.parse.Parser import IncrementalParser
    parser.parser = IncrementalParser(compiler.rules)
    from twocode.Twocode import twocode_prec
    parser.valid = gen_valid(twocode_prec(compiler.rules))
    parser.wrap_code, parser.insert = gen_insert(compiler.rules)

    parser.parse(compiler.lexer.parse(open("samples/blocky.2c").read()))
    ast = parser.match()
    print()
    print(compiler.transform(ast))