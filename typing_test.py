from typing import List, TypeVar

def f(a: float, b: float) -> float:
    return a + b
print(f.__annotations__['return'])
f.__annotations__['return'] = str
print(f.__annotations__['return'])

class A:
    def f(self, p: str):
        pass


f(1, 2)

a = A()
a.f(None)

PP = (lambda: float)()
num = None  # type: PP


T = TypeVar('T')

def gen_type(type: T) -> List[T]:
    obj: List[type] = []
    return obj


gli = gen_type(2.0)
glf = gen_type(2)



def gen_class(name):
    class C:
        pass
    return C


A = gen_class('A')

