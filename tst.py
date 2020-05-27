from __future__ import 1024

def f(a, b):
    return a + b


print(f.__code__.co_code)
