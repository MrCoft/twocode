def shared_str(s1, s2):
    len = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            len += 1
        else:
            break
    return len

escape_table = {eval('"\\{}"'.format(c)): c for c in "\\abfnrtv"}
def escape(s, max_length=80):
    ret = []

    # Try to split on whitespace, not in the middle of a word.
    split_at_space_pos = max_length - 10
    if split_at_space_pos < 10:
        split_at_space_pos = None

    position = 0

    quote = '"'
    if '"' in s and "'" not in s:
        quote = "'"
    ret.append(quote)
    position += 1
    for c in s:
        newline = False
        if c == quote:
            to_add = "\\" + quote
        elif c in escape_table:
            to_add = "\\" + escape_table[c]
        elif ord(c) < 32 or 0x80 <= ord(c):
            to_add = "\\x" + format(ord(c), "x").rjust(2, "0")
        else:
            to_add = c

        ret.append(to_add)
        position += len(to_add)
        if newline:
            position = 0

        if split_at_space_pos is not None and position >= split_at_space_pos and " \t".find(c) != -1:
            ret.append("\\\n")
            position = 0
        elif position >= max_length:
            ret.append("\\\n")
            position = 0

    ret.append(quote)

    return "".join(ret)