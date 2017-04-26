import sys

class fail_check:
    def __init__(self, get, check=lambda old, new: old != new, error=lambda: Exception("Check failure")):
        self.get = get
        self.check = check
        self.error = error
        self.old = None
    def __bool__(self):
        new = self.get()
        if self.old is None:
            self.old = new
        else:
            if self.check(self.old, new):
                self.old = new
            else:
                self.old = None
                raise self.error()
        return True

def skip_exc_info(exc_info=None, depth=0):
    if not exc_info:
        exc_info = sys.exc_info()
    exc_class, exc, tb = exc_info
    if depth >= 0:
        for i in range(depth):
            if tb.tb_next:
                tb = tb.tb_next
            else:
                break
    else:
        tbs = []
        while True:
            tbs.append(tb)
            if tb.tb_next:
                tb = tb.tb_next
            else:
                break
        depth = max(-len(tbs), depth)
        tb = tbs[depth]
    return exc_class, exc, tb

def filter(*fs):
    def f(item):
        for f in fs:
            item = f(item)
        return item
    return f