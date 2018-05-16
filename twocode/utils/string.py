from twocode import utils
import io

def shared_str(s1, s2):
    len = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            len += 1
        else:
            break
    return len

def parse_indent(text):
    indentation = [utils.leading_ws(line) for line in text.splitlines() if line.strip()]

    indents, dedents = [], []
    stack = []
    last_indent = ""
    for ws in indentation:
        last_len = len(last_indent)
        dedent = 0
        if not ws.startswith(last_indent):
            shared_len = shared_str(ws, last_indent)
            while last_len > shared_len:
                last_len -= stack.pop()
                dedent += 1
        indent = ws[last_len:]
        indents.append(indent)
        dedents.append(dedent)
        if indent:
            stack.append(len(indent))
        last_indent = ws

    return indents, dedents

def min_indent(text):
    lines = text.splitlines()
    if not lines:
        return 0
    indentation = [utils.leading_ws(line) for line in lines if line.strip()]
    if not indentation:
        return min(len(line) for line in lines)
    shared_indent = [shared_str(line1, line2) for line1, line2 in zip(indentation[:-1], indentation[1:])]
    if not shared_indent:
        return len(indentation[0])
    return min(shared_indent)

def analyze_indent(text):
    min_len = min_indent(text)
    indents, dedents = parse_indent(text)
    char_uses = {char: 0 for char in set(indents)}
    stack = []
    for indent, dedent in zip(indents, dedents):
        for i in range(dedent):
            stack.pop()
        if indent:
            stack.append(indent)
        for char in stack:
            char_uses[char] += 1
    char, uses = " " * 4, 0
    for c, u in sorted(char_uses.items()):
        if u > uses:
            uses = u
            char = c

    return min_len, char

def dedent(text):
    min_len = min_indent(text)
    return "\n".join(line[min_len:] for line in text.splitlines())

escape_table = {eval('"\\{}"'.format(c)): c for c in "\\abfnrtv"}
def escape(s, max_length=80):

    # Try to split on whitespace, not in the middle of a word.
    split_at_space_pos = max_length - 10
    if split_at_space_pos < 10:
        split_at_space_pos = None

    position = 0
    quote = None

    buf = io.StringIO()
    position += 1
    for c in s:
        newline = False

        if not quote:
            if c == '"':
                quote = "'"
            elif c == "'":
                quote = '"'

        if c == quote:
            to_add = "\\" + quote
        elif c in escape_table:
            to_add = "\\" + escape_table[c]
        elif ord(c) < 32 or 0x80 <= ord(c):
            to_add = "\\x" + format(ord(c), "x").rjust(2, "0")
        else:
            to_add = c

        buf.write(to_add)
        position += len(to_add)
        if newline:
            position = 0

        if split_at_space_pos is not None and position >= split_at_space_pos and " \t".find(c) != -1:
            buf.write("\\\n")
            position = 0
        elif position >= max_length:
            buf.write("\\\n")
            position = 0
    if not quote:
        quote = '"'

    return quote + buf.getvalue() + quote

def join(iterable, delim, width=80):
    buf = io.StringIO()
    iterable = iter(iterable)
    item = next(iterable)
    buf.write(item)
    line_len = len(item)
    for item in iterable:
        buf.write(delim)
        line_len += len(delim)
        if line_len + len(item) + len(delim) > width:
            buf.write("\n")
            line_len = 0
        buf.write(item)
        line_len += len(item)
    return buf.getvalue()
