from twocode.Tests import *

tests_class = name_tests(
    repr_null=interacts('''
        >>> null
        >>> 2
        2
    '''),
    input_cont=interacts('''
        >>> 1 +
        ... 2
        3
    '''),
    macro_arg=interacts('''
        >>> func f(x): return x
        func(x): return x
        >>> func g(macro x): return x
        func(macro x): return x
        >>> f(1 + 2)
        3
        >>> g(1 + 2)
        macro 1 + 2
        >>> @f 1 + 2
        3
        >>> @g 1 + 2
        macro 1 + 2
    '''),
    # context.call signature
    # - function with an arg called obj
    # - with the context.call(obj, *args, **kwargs) signature, this fails
    func_sign_obj=interacts('''
        >>> (func(obj): return obj)(2)
        2
    '''),
    # prec=num_parses("1 + 2 * 3"),

    affix=interacts('''
        >>> var i = 0
        >>> i++
        0
        >>> i
        1
        >>> ++i
        2
        >>> i
        2
    '''),
    sign_neg=evals("-1"),
    sign_pos=evals("+1", "1"),
)
# fails("1+")



# factorial
# node_type travel





'''
type A:
    var x = 2
    func f():
        return x
a = A()
print(a.f())
a.x = 3
print(a.f())
'''

'''
type A:
    var x = 2
    func f():
        return this.x
a = A()
a.x = 3
print(a.f())
'''
'''
var a = 2
a
a = 3
a
'''
'''
func f():
    var x = 2
    return x
f()
x
'''
'''
type A:
    func f():
        return x
a = A()
var x = 3
print(a.f())
'''

'''
type A: {}
type: var x:A
repr B
'''





# (*macro nodes)(1, 2)
# (macro 1, macro 2)
'''
    >>> in Object(): var x = 2
    >>> in Scope(): var x = 2
    >>> in Module(): var x = 2

    cls
    in macro
'''

# Null is () and is not printed specially in some repr cases
# func():{} func()->Null:{} and ()->{} are identical, of type Func<Null, Null>