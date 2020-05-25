
class IntIterator:
    def __init__(self, min=None, max=None):
        if min == None:
            min = None
        if max == None:
            max = None
        self.max = None
        self.pos = None
        self.pos = min
        self.max = max

    def has_next(self):
        return self.pos < self.max
    def next(self):
        return self.pos++

class IntRange:
    def __init__(self, min=None, max):
        if min == None:
            min = None
        self.max = None
        self.min = None
        self.min = min
        self.max = max

    def iter(self):
        return IntIterator(self.min, self.max)
