import textwrap
import twocode.utils.string

LOG = set()
LOG.add("DEBUG")

def block(text, indent=False):
    text = textwrap.dedent(text).lstrip("\r\n").rstrip()
    if indent:
        text = textwrap.indent(text, " " * 4)
    return text

class ParserGen:
    def __init__(self):
        self.rules = []
        self.lex_lang = None
    def form_parser(self):
        self.analyze()
        self.gen_states()
        self.gen_code()
    def analyze(self):
        self.symbols = []
        for rule in reversed(self.rules):
            if rule.symbol not in self.symbols:
                self.symbols.insert(0, rule.symbol)
        self.symbol_rules = {}
        for rule in self.rules:
            self.symbol_rules.setdefault(rule.symbol, []).append(rule)
        self.tokens = "WS ID EOL ENTER LEAVE".split()
        sort = lambda list: sorted(sorted(list), key=len)
        for keyword in sort(self.lex_lang.keywords):
            self.tokens.append("'" + keyword + "'")
        raw = set(self.lex_lang.raw)
        for group in self.lex_lang.ops.values():
            for item in group:
                for char in item:
                    raw.add(char)
        for item in sorted(raw):
            self.tokens.append("'" + item + "'")
        for name in sort(self.lex_lang.literals):
            self.tokens.append("LITERAL_" + name)

        self.rule_pattern = {}
        self.rule_name = {}
        import string
        legal_id = "_" + string.digits + string.ascii_letters
        for rule in rules:
            pattern = " ".join("{}[{},{}]".format(symbol.name, symbol.next, symbol.skip if symbol.skip is not None else "") for symbol in rule.pattern)
            self.rule_pattern[rule] = pattern

            pattern = [symbol.name for symbol in rule.pattern]
            if rule.symbol != "_WS":
                pattern = [symbol for symbol in pattern if symbol != "_WS"]
            pattern = [rule.symbol] + pattern
            pattern = [symbol.strip("_'") for symbol in pattern]
            name = "_".join(pattern)
            name = "".join((c if c in legal_id else "x" + format(ord(c), "x")) for c in name)
            name = name.lower()
            self.rule_name[rule] = name
    def gen_states(self):
        gen = self
        class State:
            def __init__(self):
                self.rule = None
                self.use_label = True
            def comment(self): pass
            def label(self): pass
            def code(self): pass
            def debug(self): pass
            def __str__(self):
                lines = []
                lines.extend("// " + line for line in self.comment().splitlines())
                if "DEBUG" in LOG:
                    msg = self.debug()
                    if msg:
                        lines.append('print_state(); cout << {} << endl << endl;'.format(twocode.utils.string.escape(msg)))
                lines.extend(self.code().splitlines())
                lines = [" " * 4 + line for line in lines] # format of the msg
                if self.use_label:
                    lines.insert(1, self.label() + ":")
                return "\n".join(lines)
        class ParseSymbol(State):
            def __init__(self):
                super().__init__()
                self.symbol = None
            def comment(self):
                return "PARSE " + self.symbol.upper()
            def label(self):
                return "label_parse_{}".format(self.symbol.lower())
        class RuleStart(State):
            def comment(self):
                return "RULE\n" + self.rule.symbol.upper() + " -> " + gen.rule_pattern[self.rule].upper()
            def label(self):
                return "label_{}".format(gen.rule_name[self.rule])
            def code(self):
                return ""
        class Symbol(State):
            def __init__(self):
                super().__init__()
                self.pos = None

                self.next_target = None
                self.fail_target = None
            def label(self):
                return "label_{}_{}".format(gen.rule_name[self.rule], self.pos)
            def debug(self):
                return block("""
                    Symbol:
                        Type: {}
                        Symbol: {}
                        Rule: {}
                        Pos: {}
                """.format(
                    type(self).__name__,
                    self.rule.pattern[self.pos].name,
                    str(self.rule),
                    self.pos,
                ))
        class Nonterminal(Symbol):
            def __init__(self):
                super().__init__()
                self.target = None
                # self.table_target = None
            def comment(self):
                return self.rule.pattern[self.pos].name.upper()
            def code(self):
                stack_lines = []
                stack_lines.append("*next_stack_ptr++ = &&{};".format(self.next_target.label()))
                if self.fail_target is not gen.last_rule_fail:
                    stack_lines.append("*fail_stack_ptr++ = &&{};".format(self.fail_target.label()))
                    stack_lines.append("*buffer_stack_ptr++ = buffer_ptr;")
                return block("""
                    {}

                    goto {};
                """).format("\n".join(stack_lines), self.target.label())
                # """.format(self.table_target * 2, gen.goto_table_items[self.table_target], self.target.label()))
                # is saying += 4 instead an optim?
        class Terminal(Symbol):
            def __init__(self):
                super().__init__()
                self.n = 1
                self.first = False
            def comment(self):
                return self.rule.pattern[self.pos].name
            def code(self):
                symbol = self.rule.pattern[self.pos].name
                lines = []
                lines.append(block("""
                    if (*buffer_ptr != {}) {{
                        goto {};
                    }}
                    buffer_ptr++;
                """.format(gen.tokens.index(symbol), self.fail_target.label())))
                # don't goto and just do it if it's "last rule" ?
                states = gen.rule_states[self.rule]
                if self.next_target is not states[states.index(self) + 1]:
                    lines.append("goto {};".format(self.next_target.label()))
                return "\n".join(lines)
            """
                single, last:

                multiple, last:
                if (token != TOKEN) or
                if (fetch == TOKEN)
                    goto table[stack[--its size]]

                    this is on the last, creation: goto table[stack[--its size] + 2]


                single, before nonterminal:
                if (token != TOKEN)

                multiple, before nonterminal:
                if (token != TOKEN or
                if (token != TOKEN)
                {}
            """
        class CreateSymbol(State):
            def comment(self):
                return "CREATE " + self.rule.symbol.upper()
            def label(self):
                return "label_{}_create".format(gen.rule_name[self.rule])
            def code(self):
                return block("""
                    // ast[ast_ptr++] = {};
                    // reinterpret_cast<*>(&)    ASSIGN THE FIRST NODE
                    /*
                    if (goto_table[*--stack_ptr] != &&label_last_rule_fail)
                        *history_stack_ptr++ = *stack_ptr; // optim?
                        // need buffer pos as well
                    */
                    goto **--next_stack_ptr;
                """.format(self.rule.symbol)) # TODO: history dead?
                # lets ignore this for now
                """
                    *ast_ptr++ = node_ptr
                """
            def debug(self):
                return "Created {}".format(self.rule.name)

        self.states = []
        self.symbol_states = {}
        self.rule_states = {}
        for symbol in self.symbols:
            state = ParseSymbol()
            state.symbol = symbol
            self.symbol_states[symbol] = state
            self.states.append(state)
            for rule in self.symbol_rules[symbol]:
                self.rule_states[rule] = []
                state = RuleStart()
                state.rule = rule
                self.rule_states[rule].append(state)
                for pos, symbol in enumerate(rule.pattern):
                    if symbol.name in self.symbols:
                        state = Nonterminal()
                    else:
                        state = Terminal()
                    state.rule = rule
                    state.pos = pos
                    self.rule_states[rule].append(state)
                state = CreateSymbol()
                state.rule = rule
                self.rule_states[rule].append(state)
                self.states.extend(self.rule_states[rule])

        # cmp_lines

        state = State()
        state.comment = lambda: "LAST RULE FAIL"
        state.label = lambda: "label_last_rule_fail"
        state.code = lambda: block("""
            // buffer_ptr = *--buffer_stack_ptr;
            // ast_ptr = ast_stack[--its size]
            goto **--fail_stack_ptr;
        """) # TODO: history dead
        self.last_rule_fail = state
        self.states.append(state)

        for symbol in self.symbols:
            for r, rule in enumerate(self.symbol_rules[symbol]):
                for (pos, state), s in zip(list(enumerate(self.rule_states[rule]))[1:-1], rule.pattern):
                    state.next_target = self.rule_states[rule][pos + s.next]
                    if s.skip:
                        state.fail_target = self.rule_states[rule][pos + s.skip]
                    else:
                        r_target = r + 1
                        if r_target < len(self.symbol_rules[symbol]):
                            state.fail_target = self.rule_states[self.symbol_rules[symbol][r_target]][0]
                        else:
                            state.fail_target = self.last_rule_fail
                    if isinstance(state, Nonterminal):
                        state.target = self.symbol_states[s.name]

        redirect = {}

        # TRANSFORM: remove ParseSymbols and RuleStarts, nonterminals point to first symbol of first rule instead
        for symbol in self.symbols:
            self.states.remove(self.symbol_states[symbol])
            for rule in self.symbol_rules[symbol]:
                self.rule_states[rule][0].use_label = False
        for symbol in self.symbols:
            redirect[self.symbol_states[symbol]] = self.rule_states[self.symbol_rules[symbol][0]][0]
            for rule in self.symbol_rules[symbol]:
                redirect[self.rule_states[rule][0]] = self.rule_states[rule][1]

        # TRANSFORM: L-recursion
        # NOTE: we sort the rules, putting L-recursive rules at the end
        lrecur = {}
        for symbol, s_rules in self.symbol_rules.items():
            lrecur_rules = []
            for rule in s_rules:
                if rule.pattern[0].name == symbol:
                    lrecur_rules.append(rule)
            for rule in lrecur_rules:
                s_rules.remove(rule)
            if lrecur_rules:
                lrecur[symbol] = len(s_rules)
            s_rules.extend(lrecur_rules)

            if lrecur_rules:
                lrecur_states = []
                for rule in lrecur_rules:
                    lrecur_states.extend(self.rule_states[rule])
                for state in lrecur_states:
                    self.states.remove(state)
                index = self.states.index(self.rule_states[s_rules[lrecur[symbol] - 1]][-1])
                self.states = self.states[:index + 1] + lrecur_states + self.states[index + 1:]

                for r, rule in enumerate(s_rules):
                    for state, s in zip(self.rule_states[rule][1:-1], rule.pattern):
                        if not s.skip:
                            r_target = r + 1
                            if r_target < len(s_rules):
                                state.fail_target = self.rule_states[s_rules[r_target]][0]
                            else:
                                state.fail_target = self.last_rule_fail

        # NOTE:
        class CreateSymbolGoToLRecur(CreateSymbol):
            def __init__(self):
                super().__init__()
                self.target = None
            def comment(self):
                return "CREATE " + self.rule.symbol.upper() + ", GO TO L-RECUR"
            def code(self):
                return block("""
                    goto {};
                """).format(self.target.label())
            def debug(self):
                return "Created {}, going to L-recur".format(self.rule.name)
        class CreateLRecur(CreateSymbol):
            def __init__(self):
                super().__init__()
                self.target = None
            def comment(self):
                return "CREATE " + self.rule.symbol.upper() + ", REPEAT L-RECUR"
            def code(self):
                return block("""
                    goto {};
                """.format(self.target.label()))
            def debug(self):
                return "Created {}, repeating L-recur".format(self.rule.name)
        for symbol in self.symbols:
            if symbol in lrecur:
                first_lrecur = lrecur[symbol]
                lrecur_target = self.rule_states[self.symbol_rules[symbol][first_lrecur]][0]
                for r, rule in enumerate(self.symbol_rules[symbol]):
                    create_state = self.rule_states[rule][-1]
                    create_lrecur_state = CreateSymbolGoToLRecur() if r < first_lrecur else CreateLRecur()
                    create_lrecur_state.rule = rule
                    create_lrecur_state.target = lrecur_target
                    self.rule_states[rule][-1] = create_lrecur_state
                    self.states[self.states.index(create_state)] = create_lrecur_state
                    redirect[create_state] = create_lrecur_state

        # merge in for symbol?
        # NOTE:
        state = State()
        state.comment = lambda: "L-RECUR FAIL"
        state.label = lambda: "label_lrecur_fail"
        state.code = lambda: block("""
            goto **--next_stack_ptr;
        """) # TODO: not that simple
        # possibly inlined later, like the other node
        self.lrecur_fail = state
        self.states.append(state)
        for symbol in self.symbols:
            if symbol in lrecur:
                first_lrecur = lrecur[symbol]
                lrecur_target = self.rule_states[self.symbol_rules[symbol][first_lrecur]][0]
                for state in self.rule_states[self.symbol_rules[symbol][first_lrecur - 1]]:
                    if isinstance(state, Symbol):
                        if state.fail_target is lrecur_target:
                            state.fail_target = self.last_rule_fail
                for state in self.rule_states[self.symbol_rules[symbol][-1]]:
                    if isinstance(state, Symbol):
                        if state.fail_target is self.last_rule_fail:
                            state.fail_target = self.lrecur_fail
        # maybe move/jump

        # NOTE: remove first state of L-recursive rules
        class CommentState(State):
            def __init__(self):
                super().__init__()
                self.cmnt = None
                self.desc = None
                self.use_label = False
            def comment(self):
                return self.cmnt
            def code(self):
                return block("""
                    /*
                        {}
                    */
                """).format(self.desc)
        for symbol in self.symbols:
            if symbol in lrecur:
                for rule in self.symbol_rules[symbol][lrecur[symbol]:]:
                    lrecur_state = self.rule_states[rule][1]
                    cmnt_state = CommentState()
                    cmnt_state.cmnt = lrecur_state.comment()
                    cmnt_state.desc = "removed first state of L-recursive rule"
                    self.rule_states[rule][1] = cmnt_state
                    self.states[self.states.index(lrecur_state)] = cmnt_state
                    redirect[lrecur_state] = self.rule_states[rule][2]
                    redirect[cmnt_state] = self.rule_states[rule][2]

        # AND we remove everything that isn't a target in any way
        # remove unused labels
            # probably - nodes followed by terminals
            # gototable has to ask whether its used or not

        # instead of target state, it's a Jump   Move?
            # so we can do "goto thing" -> the code itself
            # or a null if it just follows?

        # TRANSFORM: redirect
        for state in self.states:
            if isinstance(state, Symbol):
                while state.fail_target in redirect:
                    state.fail_target = redirect[state.fail_target]
            if hasattr(state, "target"):
                while state.target in redirect:
                    state.target = redirect[state.target]

        if False:
            # TRANSFORM: goto table
            self.goto_table = []
            self.goto_table_items = []
            num_items = 0
            for symbol in self.symbols:
                #for r, rule in enumerate(self.symbol_rules[symbol]): # [:-1] because tail rec?
                #    # for nonterminal states?
                for rule in self.symbol_rules[symbol]:
                    goto_lines = []
                    for state in self.rule_states[rule]:
                        if isinstance(state, Nonterminal):
                            state.table_target = num_items
                            goto_lines.append("&&{}, &&{},".format(state.fail_target.label(), state.next_target.label()))
                            num_items += 1
                    if goto_lines:
                        self.goto_table.append("// {} -> {}".format(symbol.upper(), self.rule_pattern[rule]))
                        self.goto_table.extend(goto_lines)
                        for line in goto_lines:
                            fail_target, next_target = line.translate({ord("&"): None}).rstrip(",").split(", ")
                            self.goto_table_items.append((next_target, fail_target))

        # filters:
        # only first buffer[buffer_ptr] is token
            # ast creation should happen at the end - it makes it non continuous but creates it far less often
            # can you even do it though? it's not like you can create a var for it and make it last
            # that would break on the var being used twice
        # merge terminal tokens

            # merges - asking for lots of terminals -> better comparison
            # many rules starting with the same sequence -> a shared start
            # shared "subsequences" -> would work if you store some sort of state
                # care that literally anything can stack
            # comment these, AND other things we've done
            # goto_table_items, methods, debug

    def gen_code(self):
        parts = []
        parts.append(block("""
            #include <iostream>
            #include <fstream>
            #include <map>
            using namespace std;

            unsigned char buffer[256];
            void parse();

            int main() {
                ifstream file("tokens.bin", ios::in | ios::binary | ios::ate);
                if (!file.is_open())
                    throw runtime_error("error opening file");
                streampos size = file.tellg();
                // buffer = new unsigned char[size];
                file.seekg(0, ios::beg);
                file.read(reinterpret_cast<char*>(buffer), size);
                file.close();

                // DEBUG: print
                // for (unsigned int i = 0; i < size; i++)
                //     cout << static_cast<unsigned>(buffer[i]) << endl;

                parse();
            }

            unsigned char* buffer_ptr;
            unsigned char token;

            void* next_stack[1024];
            void** next_stack_ptr = next_stack;
            void* fail_stack[1024];
            void** fail_stack_ptr = fail_stack;
            unsigned char* buffer_stack[1024];
            unsigned char** buffer_stack_ptr = buffer_stack;

            // debug
            unsigned char history_stack[1024];
            unsigned char* history_stack_ptr = history_stack;
        """))

        parse_parts = []
        if False:
            parse_parts.append(block("""
                void* goto_table[] = {{
                    {}
                }};
            """, indent=True).format(textwrap.indent("\n".join(self.goto_table), " " * 8).lstrip())
            )
        if "DEBUG" in LOG:
            stack_str_table = ",\n".join(['{{&&{}, "{}"}}'.format(state.label(), state.label()) for state in self.states if state.use_label])
            stack_str_table = textwrap.indent(stack_str_table, " " * 8).lstrip()
            parts.append(block("""
                static map<void*, string> stack_str;
            """))
            parse_parts.append(block("""
                stack_str = {{
                    {}
                }};
            """, indent=True).format(stack_str_table.lstrip()))
        parse_parts.append("\n\n".join(str(state) for state in self.states))
        parts.append(block("""
            void parse() {{
                buffer_ptr = buffer;
                token = *buffer_ptr;

                {}
            }}
        """).format("\n\n".join(parse_parts).lstrip()))

        if "DEBUG" in LOG:
            token_str_table = twocode.utils.string.join(('/*{}*/"{}"'.format(index, token) for index, token in enumerate(self.tokens)), ", ", 80 - 4)
            token_str_table = "\n".join([" " * 4 + line.rstrip() for line in token_str_table.splitlines()])
            parts.insert(-1, block("""
                static constexpr const char* token_str[] = {{
                    {}
                }};
            """).format(token_str_table.lstrip()))

            if False:
                stack_str_table = "\n".join(['"({}, {})",'.format(next_target, fail_target) for next_target, fail_target in self.goto_table_items])
                stack_str_table = textwrap.indent(stack_str_table, " " * 4).lstrip()
                parts.insert(-1, block("""
                    static constexpr const char* stack_str[] = {{
                        {}
                    }};
                """).format(stack_str_table.lstrip()))

                history_str_table = "\n".join(['"{}",'.format(fail_target) for next_target, fail_target in self.goto_table_items])
                history_str_table = textwrap.indent(history_str_table, " " * 4).lstrip()
                parts.insert(-1, block("""
                    static constexpr const char* history_str[] = {{
                        {}
                    }};
                """).format(history_str_table.lstrip()))

            parts.insert(-1, block("""
                static const char* delim = "{}";
                void print_state() {{
                    cout << "State:" << endl;

                    cout << delim << "Buffer:" << endl;
                    cout << delim << delim << "Pos: " << static_cast<unsigned>(buffer_ptr - buffer) << endl;
                    cout << delim << delim << "Tokens: [" << token_str[*buffer_ptr];
                    for (unsigned int i = 1; i < 3; i++) cout << ", " << token_str[*(buffer_ptr + i)];
                    cout << ",..]" << endl;

                    cout << delim << "Stack:" << endl;
                    /*
                    cout << delim << delim << "Size: " << static_cast<unsigned>(stack_ptr - stack) << endl;
                    cout << delim << delim << "Targets:" << endl;
                    for (unsigned char* s = stack; s < stack_ptr; s++) {{
                        cout << delim << delim << delim << stack_str[(*s) >> 1] << endl;
                    }}
                    */
                    cout << delim << delim << "Buffer: [";
                    for (unsigned char** b = buffer_stack; b < buffer_stack_ptr; b++) {{
                        cout << static_cast<unsigned>(*b - buffer);
                        if (b < buffer_stack_ptr - 1)
                            cout << ", ";
                    }}
                    cout << "]" << endl;

                    // debug
                    /*
                    cout << delim << delim << "History:" << endl;
                    for (unsigned char* h = history_stack; h < history_stack_ptr; h++) {{
                        cout << delim << delim << delim << history_str[(*h) >> 1] << endl;
                    }}
                    */

                    cout << delim << delim << "Next Stack:" << endl;
                    for (void** s = next_stack; s < next_stack_ptr; s++) {{
                        cout << delim << delim << delim << stack_str.at(*s) << endl;
                    }}
                    cout << delim << delim << "Fail Stack:" << endl;
                    for (void** s = fail_stack; s < fail_stack_ptr; s++) {{
                        cout << delim << delim << delim << stack_str.at(*s) << endl;
                    }}

                    cout << endl;
                }}
            """).format("\t".replace("\t", " " * (4)))) # TODO: history
            # cout << delim << delim << delim << stack_str[s] << endl;
            # insert an eleemnt. wat

        code = "\n\n".join(parts) + "\n"
        with open("parser.cpp", "w", encoding="utf-8") as file:
            file.write(code)

        # optim: why have multiple ws states? group them, do a single comparison
        # the initial loadout?

        # terminals don't pass to the next rule
        # i'd like if i could print the tokens as well, we're SO CLOSE
        # .\t stack
        # print before every goto?

        # LL is stack + parse table?

        # we're not producing 2c->c++ target
        # this does not need to be super-efficient
        # really, it should be this just because i worked on it so hard
        # improvements can come later, 0.5 needs to finish with >A< parser

if __name__ == "__main__":
    from twocode.parser.lexer import example_lex
    from twocode.parser.state_parser import example_grammar
    import twocode.parser.state_parser
    twocode.parser.state_parser.LOG.update(LOG)

    lex_lang = example_lex()
    grammar = example_grammar()
    lex_model = lex_lang.form_model()
    lexer = lex_model.form_lexer()

    grammar.ops = lex_lang.ops
    grammar.literals = lex_lang.literals
    rules = grammar.form_rules()

    parser_gen = ParserGen()
    parser_gen.rules = rules
    parser_gen.lex_lang = lex_lang
    parser = parser_gen.form_parser()

    with open("samples/test.txt") as file, open("tokens.bin", "wb") as tokens:
        for token in lexer.parse(file.read()):
            char = parser_gen.tokens.index(token.type)
            tokens.write(bytes([char]))

    import os
    os.system(" ".join([
        "g++",
        "-std=c++14",
        "-O3",
        "parser.cpp",
        "-s",               # NOTE: equivalent of strip
        "-o parser.exe",
    ]))
    os.system(" ".join([
        "strip",
        "--strip-unneeded", # NOTE: it's larger if not first
        "-s",
        "-R .comment",
        "-R .gnu.version",
        "parser.exe",
    ]))
    os.system("parser.exe > output.txt")
    exit()

    import subprocess
    process = subprocess.Popen("parser.exe", stdin=subprocess.PIPE)
    with open("samples/test.txt") as file:
        for token in lexer.parse(file.read()):
            char = parser_gen.tokens.index(token.type)
            process.stdin.write(bytes([char]))

# buffer fallback doesn't work
# -funroll-loops

# parser neural network?
# a tiny nn that fits into memory, executed by the cpu
# so that the stream of tokens is compressed (likeliness of a token based on last 3 tokens)



# buffer_ptr is unrelated to stack, it's a list of failures and is quite larger
# ws loop

# a way to insert some directives? templates? string replace
# #define getmax(a,b) ((a)>(b)?(a):(b))
# used directives:

# pointer > array indexing
    # known memory location is faster than having to calculate it first from the address of the starting element
# stacks to vectors
# debugging done now! and it still doesn't work
# c 17?







# c11 has max 4095 characters per line

# start with the symbol to parse(expr)
# recursion by pointing to the item in the ast to replace

# 6. cparser
    # we almost never use two at once
    # it needs a "crash" symbol though
    # so that it stops parsing

# how much are you fetching stuff? because tables suddenly seem better now
# you apply a goto to jump to code that literaly differs in... the terminal it compares it to
    # and the part of the table it sends you off to?
    # wouldn't a SINGLE LOOP + data table be better?

# perf - it prints its time of total parse
# debug also ends with number of parses


# last lrecur creation might just chill though
# any manual goto whose target immediately follows
    # there might be non-code states between




#also, IP's strength is that it can tell you what would be the next legal tokens
#    include it somehow? would it make it faster - we're sharing everything, why not share leafs?
# nah, just the idea of 2-way sharing (top down and bottom up)














# when you fail the entire stack, you backtrack by 1 and try a different combination
# HOW? buffer_ptr?


# entire stack / a decision while building a node

# since the node is built when done, and all i care about is its parent actually...

# the history points to the node
# the node points to its parent and to the state


# the history is of
# buffer pos


# pointer to a parent node - not a decision, but an ast layer
# pointer to a parent decision
# pointer to an equivalent decision



# stack of past decisions:
# a different way of building file
# a different way of building file_content
# _WS_create, NO LRECUR
    # if it created the ws off WS->ENTER (1st), it might still try 2nd, although we know its nonsense?
# _WS_create, NO LRECUR


# when, what to push
# if it had skip, skip it
# lrecur - don't
# after creation of a rule, try the next rule

# the state:
# the exact stack, position

# order - skip, creation, lrecur(same as creation)


# the next decision branch points to this



















# lrecur fail?




"""
State:
    Buffer:
        Pos: 1
        Tokens: [WS, ID, EOL,..]
    Stack:
        Size: 2
        Targets:
            (label_file_file_content_eol_file_content_1, label_last_rule_fail)
            (label_file_content_class_create, label_last_rule_fail)
        Buffer: [0, 0]
        History:
"""

"""
State:
    Stack:
        Next:
        Fail:


        cmd/state

        buffer pos
        the fail it is about to remove
        pointer to next rule

        cmd state reconstruction?
"""

# NAMING: Targets / Next:
# Rollback / History / Fail

# create symbol pushes to fail
# there's no if, it knows?



# rework last rule fail to pop and restore

# c++ map literal?


# map<string, int> mymap = {{"one", 1}, {"two", 2}, {"three", 3}};

# history-bound variables
# their api has opposite calls, every use of one pushes an opposite command to a list
# where you can create checkpoints
# and call "rollback" which rolls all of them back
"""
    var a = []
    var b = []
    var h = History(a, b)

    a.extend([1, 2, 3])
    b.push("a")
    h.checkpoint()

    a.push(4)
    b.pop()

    a, b
    ([1, 2, 3, 4], [])

    h.rollback()
    a, b
    ([1, 2, 3], ["a"])

    h.rollback()
    a, b
    ([], [])

    class HistoryList:
        func __init__(list, history):

        func push(item):
            list.push(item)
            history.push(HistoryCmdPop)
        func pop():
            list.pop()
            history.push(HistoryCmdPush(item))
"""


# the map - static? set?
# and aren't they... copied? managing the change
# remove old stacks

# Created _WS_append, repeating L-recur
# LIAR

# map out of range after creating 100mb of output
# lrecur fail is silent

#

# http://www.cplusplus.com/forum/beginner/46712/