from twocode.utils.node import Node, range_call, l
import textwrap
from twocode.utils.code import format_exception_only
from twocode import utils
import twocode.utils.string

LOG = set()
#LOG.add("PERF")

stmt_symbol = "stmt"
delims = ['EOL', "';'"]
ws = "WS EOL ENTER LEAVE".split()

class IndentParser:
    def __init__(self):
        self.parser = None
        self.valids = []
        self.wrap_code, self.insert = None, None
        if "PERF" in LOG:
            self.log = utils.Object(
                edge=[],
                expand_volume=[],
                tree_size=[],
            )
    def validate(self, node):
        for valid in self.valids:
            valid(node)
    def parse(self, lexer):
        buffer = list(lexer)
        if "PERF" in LOG:
            for key in self.log:
                self.log[key] = [None for i in range(len(buffer))]
        # REMOVED: breaks if inner parser becomes dirty
        # self.parser.init_search()
        self.num_parses = 1
        code, self.errors = self.check(buffer)
        self.matches = [code]
    def match(self):
        if self.errors:
            raise Exception("\n".join([""] + [str(error) for error in self.errors]))
        return self.matches[0]
    def check(self, buffer, tree=None):
        if tree is None:
            tree = parse_block_tree(buffer)

        all_matches = []
        all_errors = []

        parser = self.parser.copy() # not even that necessary?
        i = tree.pos
        tree_end = tree.pos + tree.length
        def skip_ws():
            nonlocal i
            while i < tree_end and (buffer[i].type in ws or buffer[i].type in delims):
                i += 1

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

        def pack_matches():
            nonlocal matches, i

            matches_re = []
            msg = None
            for match in matches:
                try:
                    self.validate(match)
                    matches_re.append(match)
                except Exception as exc:
                    msg = format_exception_only(exc)
            matches = matches_re
            if not matches:
                if match_pos >= tree_end:
                    return
                    # REASON: pack_matches() after leaving a block prints an error at nothing
                code = " ".join(str(buffer[j]) for j in skip_subs(match_pos, match_end if msg else i, subs))
                if not msg:
                    msg = Exception("can't parse <stmt> ")
                error = "{}at: {}".format(msg, code)
                all_errors.append(error)
                return

            sub_pos = list(skip_subs(match_pos, match_end, subs))
            sub_buffer = [buffer[j] for j in sub_pos]
            sub_len = len(sub_buffer)

            #print(subs)
            #print("about to split:", sub_buffer)
            remain_match, remain_parses = matches[0], 1
            pos = 0
            matches = []
            offsets = []
            parser.init_search(stmt_symbol)
            for i1 in range(sub_len):
                parser.push(sub_buffer[i1])
                if "PERF" in LOG:
                    for key in self.log:
                        self.log[key][sub_pos[i1]] = parser.log[key][i1]
                if not (i1 + 1 >= sub_len or sub_buffer[i1 + 1].type in delims):
                    continue

                matches1 = []
                for match1 in parser.matches:
                    #try:
                        self.validate(match1)
                        matches1.append(match1)
                    #except:
                    #    continue
                if not matches1:
                    continue

                i2 = i1 + 2
                while i2 < sub_len and sub_buffer[i2].type in ws:
                    i2 += 1
                parser2 = self.parser.copy()
                parser2.init_search(stmt_symbol)
                pos2 = i2
                for i2 in range(pos2, sub_len):
                    parser2.push(sub_buffer[i2])

                matches2 = []
                for match2 in parser2.matches:
                    #try:
                        self.validate(match2)
                        matches2.append(match2)
                    #except:
                    #    continue
                if matches2:
                    matches.append(matches1[0])
                    offsets.append(sub_pos[pos])
                    self.num_parses *= len(matches1)
                    pos = pos2
                    remain_match, remain_parses = matches2[0], len(matches2)
                    if "PERF" in LOG:
                        for i in range(i1 + 1):
                            for key in self.log:
                                self.log[key][sub_pos[i]] = parser.log[key][i]
                        for i in range(pos2, i2 + 1):
                            for key in self.log:
                                self.log[key][sub_pos[i]] = parser2.log[key][i]
                    parser.init_search(stmt_symbol)
                    break
            matches.append(remain_match)
            offsets.append(sub_pos[pos])
            self.num_parses *= remain_parses
            offsets.append(sub_pos[-1] + 2)
            #print(len(matches))

            all_code = []
            for subtree in subs:
                #print("subcheck")
                code, errors = self.check(buffer, subtree)
                all_code.append(code)
                all_errors.extend(errors)

            matches_re = []
            for match, pos, end in zip(matches, offsets[:-1], offsets[1:]):
                length = end - pos - 1
                for subtree, code in reversed(list(zip(subs, all_code))):
                    if pos <= subtree.pos - 1 and subtree.pos + subtree.length <= pos + length:
                        offset = subtree.pos
                        for subtree in reversed(subs):
                            if offset > subtree.pos:
                                offset -= subtree.length
                        #print("inserting")
                        # to test before you fix this
                        self.insert(match, offset - pos, code)
                matches_re.append(match)
            all_matches.extend(matches_re)
            #print("over")
        def delim_split(): #
            pass

        def loop():
            nonlocal i, matches, match_pos, match_end
            parser.init_search(stmt_symbol)
            skip_ws()
            while i < tree_end:
                if subtree and i >= subtree.pos - 1:
                    if i >= subtree.pos:
                        raise Exception("algorithm error: skipped into subtree")
                    blocks = [branch for branch in parser.edge if branch.rule.symbol == "block_list" and not branch.node.children]
                    # note - filters out expr_term by not listing it, and block_list has no problem with either
                    # the entire motivation behind subs
                    if blocks:
                        parser.edge = blocks
                        #parser.push(buffer[i])
                        #parser.push(buffer[i + subtree.length + 1])
                        from twocode.parser import Token
                        parser.push(Token("'{'"))
                        parser.push(Token("'}'"))

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
                        # REASON: trying to merge two lines(EOL VAR >PTR<), panicking would skip the next line
                        if i < match_pos:
                            i = match_pos
                            # REASON: (EOL >PTR<) a wrong start with EOL before jumps in front of it and loops
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

                        skip_ws()
                        matches = []
                        subs.clear()
                        parser.init_search(stmt_symbol)
                        match_pos, match_end = i, None
            pack_matches()
        loop()

        return self.wrap_code(all_matches), all_errors

# which parses a token buffer to sform a tree hierarchy
# yield
def parse_block_tree(buffer, leave_token=None, pos=0):
    """
        parses into a tree of ranges, identifying nested blocks
        LEAVE has higher priority than '}' and can leave without closing some brackets
    """
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
    rule_descs = ["{} -> {}".format(rule.symbol, " ".join(symbol.name for symbol in rule.pattern if symbol.name != "_WS")) for rule in rules]
    def find_type(s):
        rule = rules[rule_descs.index(s)]
        pos_map = []
        names = [symbol.name for symbol in rule.pattern]
        pos = -1
        for symbol in rule.pattern:
            if symbol.name == "_WS":
                continue
            pos = names.index(symbol.name, pos + 1)
            pos_map.append(pos)
        return lambda *args, children_pos=None: Node(rule=rule, children_pos=pos_map[:len(args)] if children_pos is None else children_pos, children=list(args))
    block_list, code_append, code_stmt = [find_type(s) for s in textwrap.dedent("""
        block_list -> '{' code '}'
        code -> code DELIM stmt
        code -> stmt
    """).strip().splitlines()]

    def wrap_code(lines):
        if not lines:
            return block_list(Node(rule=None, token=None), Node(rule=None, token=None), children_pos=[0, 2])
        node = code_stmt(lines[0])
        for stmt in lines[1:]:
            node = code_append(node, Node(rule=None, token=None), stmt)
        node = block_list(Node(rule=None, token=None), node, Node(rule=None, token=None))
        # REASON:
        # useless fillers, but None and Node() crash the map travel,
        # and rule=None requires token=None because it is a terminal
        return node
    def insert(node, pos, code):
        def insert(node, range):
            p, len = range
            rule = node.rule
            if rule and rule.symbol == "block_list":
                if p == pos - 1:
                    return code
        range_call(l(insert))(node)
    return wrap_code, insert

def gen_valid_indent():
    def iter_tokens(node):
        for pos, child in zip(node.children_pos, node.children):
            if not child.rule:
                yield node, pos
            else:
                for n, j in iter_tokens(child):
                    yield n, j
    def tree_call(node, f):
        for child in node.children:
            tree_call(child, f)
        f(node)

    def valid(node):
        # twice?
        # print(node)
        enum_tokens = list(iter_tokens(node))
        #for n, i in enum_tokens:
        #    print(n.rule.symbol, n.rule.pattern[i], repr(n.children[i].token))
        valid_tokens_empty_line(n.rule.symbol for n, i in enum_tokens)
        for n, i in enum_tokens:
            # if n.rule.symbol == "ENTER":
            if n.rule.pattern[i].name == "ENTER":
                indent = n.children[i].token
                valid_indent_order(indent)
        indents = []
        for n, i in enum_tokens:
            rule = n.rule
            if rule.symbol == "block_list" and rule.pattern[i].name == "ENTER":
                indent = n.children[i].token
                indents.append(indent)
        for indent in indents:
            valid_indent_mixed(indent)
            valid_indent_odd(indent)
        itervalid_indent_consistent(indents)
        tree_call(node, valid_inline_block)
    return valid

def valid_indent_order(indent):
    if indent.lstrip("\t").lstrip(" "):
        raise IndentationError("spaces followed by tabs")
def itervalid_indent_consistent(indents):
    style = None
    for indent in indents:
        if style is None:
            style = indent
        else:
            if indent != style:
                raise IndentationError("inconsistent indentation({}, was {})".format(twocode.utils.string.escape(indent), twocode.utils.string.escape(style)))
def valid_indent_mixed(indent):
    if ("\t" in indent) == (" " in indent):
        raise IndentationError("mixed indentation")
def valid_indent_odd(indent):
    if " " in indent:
        if len(indent) not in [1, 2, 3, 4, 8]:
            raise IndentationError("odd number of spaces")
    else:
        if len(indent) not in [1]:
            raise IndentationError("multiple tabs")
def valid_tokens_empty_line(tokens):
    buffer = []
    error = "LEAVE EOL ENTER".split()
    for token in tokens:
        buffer.append(token)
        if len(buffer) > 3:
            buffer.pop(0)
        if buffer == error:
            raise IndentationError("blocks separated by whitespace")

def valid_inline_block(node):
    rule = node.rule
    if not rule:
        return
    if rule.symbol == "expr" and "block_list" in [symbol.name for symbol in rule.pattern]:
        assert "ENTER" not in [symbol.name for symbol in node.children[0].rule.pattern], "whitespace <expr_block>"
# last
# TESTS!
"""
either isolate the ws block rule | look for block parents, we cant sub block_list
"""
# expr block?
# rule. stuff with new grammar

if __name__ == "__main__":
    from twocode import Twocode
    twocode = Twocode()
    compiler = twocode.parser

    parser = IndentParser()
    from twocode.parser import IncrementalParser
    parser.parser = IncrementalParser(compiler.rules)
    from twocode.lang.grammar import prec
    parser.valids.append(gen_valid_indent())
    parser.valids.append(prec(compiler.rules))
    parser.wrap_code, parser.insert = gen_insert(compiler.rules)

    #parser.parse(compiler.lexer.parse(open("samples/blocky.2c").read()))
    parser.parse(compiler.lexer.parse(open("../../code/code/iter.2c").read()))
    ast = parser.matches[0]
    print()
    print(compiler.transform(ast))
    parser.match()
