import shutil
import collections

def preview(s, length=None, *, rstrip=False):
    if length is None: length = shutil.get_terminal_size().columns
    if (len(s) >= length):
        s = s[:length - 2]
        if rstrip:
            s = s.rstrip()
        s += ".."
    elif not rstrip:
        s = s.ljust(length, " ")
    return s

class Table:
    Attr = collections.namedtuple("Attr", "name, get, total")
    Attr.__new__.__defaults__ = (None,) * len(Attr._fields)
    def __init__(self, attrs):
        self.attrs = []
        for attr in attrs:
            if isinstance(attr, str):
                attr = Table.Attr(attr, lambda item: getattr(item, attr.lower()))
            elif isinstance(attr, tuple):
                attr = Table.Attr(*attr)
            self.attrs.append(attr)
        self.data = []
    def __str__(self):
        grid = [[attr.name] for attr in self.attrs]
        for item in self.data:
            for c, attr in enumerate(self.attrs):
                grid[c].append(str(attr.get(item)))
        total_line = any(attr.total for attr in self.attrs)
        if total_line:
            grid[0].append("Total")
            for c, attr in list(enumerate(self.attrs))[1:]:
                if attr.total:
                    grid[c].append(str(attr.total(self.data)))
                else:
                    grid[c].append("")
        widths = [max(len(item) for item in column) for column in grid]
        grid = [[item.ljust(width) for item in column] for column, width in zip(grid, widths)]
        lines = []
        for i in range(len(grid[0])):
            lines.append(" ".join(column[i] for column in grid))
        lines.insert(1, "=" * (sum(widths) + len(grid) - 1))
        if total_line:
            lines.insert(-1, "=" * (sum(widths) + len(grid) - 1))
        return "\n".join(lines)
