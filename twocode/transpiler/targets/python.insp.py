
#f = c.eval(c.parse('func f(a, b=2): return "xo"'))
#print(py_func(f))

cls_code = textwrap.dedent("""
    class V:
        var x:Int = 2
        var y:Int

        func __init__(_y=5):
            y = _y
        func sum():
            return x + y
""").strip()
V = c.eval(c.parse(cls_code))
# print(py_class(V))
for type in all_types:
    print(py_class(type))

result = """
    class V:
        def __init__(self, _y=5):
            self.x = 2
            self.y = None
            self.y = _y
        def sum(self):
            return x + y
""" # back into parse?

# missing: if chain