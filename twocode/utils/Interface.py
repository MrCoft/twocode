import shutil

def preview(s, length=None):
    if length is None: length = shutil.get_terminal_size().columns
    if (len(s) >= length):
        s = s[:length - 2] + ".."
    else:
        s = s.ljust(length, " ")
    return s