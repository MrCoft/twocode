import shutil

def preview(s, length=None, rstrip=False):
    if length is None: length = shutil.get_terminal_size().columns
    if (len(s) >= length):
        s = s[:length - 2]
        if rstrip:
            s = s.rstrip()
        s += ".."
    elif not rstrip:
        s = s.ljust(length, " ")
    return s
