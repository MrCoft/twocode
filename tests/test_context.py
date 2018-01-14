from twocode.Tests import *

name_tests(
    repr_null=interacts("""
        >>> null
        >>> 2
        2
    """),
    input_cont=interacts("""
        >>> 1 +
        ... 2
        3
    """),
    macro_arg=interacts("""
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
    """),
    # context.call signature
    # - function with an arg called obj
    # - with the context.call(obj, *args, **kwargs) signature, this fails
    func_sign_obj=interacts("""
        >>> (func(obj): return obj)(2)
        2
    """),
    # prec=num_parses("1 + 2 * 3"),

    affix=interacts("""
        >>> var i = 0
        >>> i++
        0
        >>> i
        1
        >>> ++i
        2
        >>> i
        2
    """),
    sign_neg=evals("-1"),
    sign_pos=evals("+1", "1"),
)
# fails("1+")



# factorial
# node_type travel


# funcs see their own args

# lshifts etc
# >>> 3
# >>> 3 <<= 3
# 24


"""
type A:
    var x = 2
    func f():
        return x
a = A()
print(a.f())
a.x = 3
print(a.f())
"""

"""
type A:
    var x = 2
    func f():
        return this.x
a = A()
a.x = 3
print(a.f())
"""
"""
var a = 2
a
a = 3
a
"""
"""
func f():
    var x = 2
    return x
f()
x
"""
"""
type A:
    func f():
        return x
a = A()
var x = 3
print(a.f())
"""

"""
type A: {}
type: var x:A
repr B
"""


"""
    >>> Func, Arg, Type, BoundMethod, Var
    >>> Func
    type:
        var args = List<Arg>()
        var code:Code
        var native:Any
        var return_type:Type

    >>> Arg
    type:
        var name = ""
        var type_ref:Type
        var default:Code
        var pack:String
        var macro = false
    >>> Type
    type:
        var __base__:Type
        var __fields__ = Map<>()
    >>> BoundMethod
    type:
        var func
        var obj
    >>> Var
    type:
        var value
        var type_ref
"""


"""
    >>> var l1 = string.parser.Lexer
    >>> import string.parser.Lexer as l2
    >>> l1 is l2

    bound to root look-up
        builtins, basic types

    basic types, eg list, written where it is, an abstract over the native
    set hard, overriding the file, erasing any possible __package__

    code
        types

    code.native.types
        native = lang.python

    math.IntRange
"""

# (*macro nodes)(1, 2)
# (macro 1, macro 2)
"""
    >>> in Object(): var x = 2
    >>> in Scope(): var x = 2
    >>> in Module(): var x = 2

    cls
    in macro
"""
# : {} works but : { } does not
#(1,) ()


# test getattr message
# test getattr message with no qualname

"""
    >>> 1, 2
    (1, 2)

    >>> var a, b = 1, 2
    >>> a, b
    (1, 2)
    >>> a
    1
    >>> b
    2

    >>> var a = (1,)
    >>> a
    1

    Tuple<Int>


    >>> var a, b, c = (()->3)(), 1 + 2, 3
    >>> a, b, c
    (3, 3, 3)

    >>> (0, 1)[0]
    0

    >>> a, b, c, d = 0, [1, 2, 3]
    >>> vec = 0, 1, 2
    >>> vec
    (0, 1, 2)

    >>> (0, 1) + (1, 2)
    (1, 3)

    >>> (0, 1) + 3  (fill by repetition)
    (3, 4)
"""

"""
var obj = Dynamic()
in obj: var x = 2
obj.x
2

methods work
"""

# partial path works???
# eg if inside a.b, import c.d is enough
# and it... walks, in what direction? of the scope?
# i think it returns a stack of a current context object and a root module


# Null is () and is not printed specially in some repr cases
# func():{} func()->Null:{} and ()->{} are identical, of type Func<Null, Null>

# methods work on their own vars
# [] prints []
# List() can be called
# native works in a class

"""
null prints nothing

C:\Python35\python.exe H:/Twocode/twocode/Twocode.py
>>> func f(n): return if n == 1: 1 else: n * f(n - 1)
null
>>> f
Traceback (most recent call last):

    tree = map[val](tree)
  File "H:\Twocode\twocode\Context.py", line 442, in term_id
    raise NameError("name {} is not defined".format(repr(id)))
NameError: name 'f' is not defined
>>> func f():{}
func(): {}
>>> f
func(): {}
>>> func f(n): {return if n == 1: 1 else n * f(n - 1)}
Traceback (most recent call last):
  File "H:/Twocode/twocode/Twocode.py", line 577, in <lambda>
    self.compile = lambda code: self.twocode.parse(code)
  File "H:\Twocode\twocode\parse\Context.py", line 20, in parse
    ast = self.parser.match()
  File "H:\Twocode\twocode\parse\IndentParser.py", line 47, in match
    raise Exception("\n".join([""] + [str(error) for error in self.errors]))
Exception:
can't parse <stmt> at: 'func' WS id("f") '(' id("n") ')' ':' WS '{' 'return' WS 'if' WS id("n") WS COMPARE("==") WS LITERAL_float("1") ':' WS LITERAL_float("1") WS 'else' WS id("n")
>>> func f(n): {return if n == 1: 1 else: n * f(n - 1)}
null
>>> f
func(): {}
>>> f(2)
Traceback (most recent call last):

    tree = map[val](tree)
  File "H:\Twocode\twocode\Context.py", line 472, in term_call
    scope = context.unpack_args(func, args)
  File "H:\Twocode\twocode\Context.py", line 99, in unpack_args
    raise SyntaxError("signature mismatch while unpacking arguments")
  File "<string>", line None
SyntaxError: signature mismatch while unpacking arguments
>>> f()
Traceback (most recent call last):

    tree = map[val](tree)
  File "H:\Twocode\twocode\Context.py", line 511, in expr_term
    type = obj.__type__
AttributeError: 'NoneType' object has no attribute '__type__'
>>>
"""

"""
    (?a) == (a=null)
"""

# a test that confirms that during none of these tests there's extra output?

# sort new twocode thing, rm load cmd

# require empty line after indent

# iterator - Intrange
# intiterator



# does the classic a() or b() work here?
# (membered)

# var a
# persistency

# with
# in enter exit

# or specify pattern matching

# fix prints

# tuples
# __this__ __native__

#    "&&=": "__iand__",
#    "||=": "__ior__",

# // ** typing, // returns int
# qualname of Int etc
# test join

# Null() constructable?
# *args **kwargs usage

# all sorts of contains

# unary eval, macro, expr

# increment priority over double unary?

# string split

# Map(a=2)

# equality of basic types

# hash impl

# test that - [1] is list, that [1, 2] is list
            # TEST THAT [(1, 2)] has length 2! it might break down wrapped tuples

# don't save a botched class/func (eg failed to eval an arg type)

#"{}".format("")
#'""'
#>>> "{}".format(null)
# "null"

#>>> eval("1+2")
#3

#class and func don't return if named
#var doesn't return anything