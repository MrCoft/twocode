from twocode.Tests import *

# var x:Float
# __new__ __default__

# List() works
    # [] printing []

name_tests(
    true = evals("true"),
    false = evals("false"),

    int = evals("2"),
    float = evals("4.5"),
    zero = evals("0"),
    add = evals("1 + 2", "3"),

    string_empty = evals('""'),
    string_simple = evals('"abc"'),
    string_multiline = interacts("""
        >>> print("a\\nb")
        a
        b
    """),

    map = interacts("""
        >>> var a = ["key1": 123, "key2": 456,]
        >>> a
        ["key1": 123, "key2": 456]
        >>> a["key1"]
        123
        >>> a["key3"] = 789
        >>> a
        ["key1": 123, "key2": 456, "key3": 789]
    """),
    map_contains = evals('"key1" in ["key1": 123]', "true"),
    map_add = evals('["key1": 123] + ["key2": 456]', '["key1": 123, "key2": 456]'),

    list = evals("[1, 2]"),
    list_empty = evals("[]"),
    list_single = evals("[1]"),
    list_tuple = evals("[1,]", "[1]"),

    tuple = evals("(1, 2)"),
    tuple_empty = evals("()"),
    tuple_single = evals("(1,)"),
    tuple_parens = evals("(1)", "1"),
    tuple_expr = evals("1, 2", "(1, 2)"),

    code = evals("macro return 2"),
    code_recur = evals("macro macro 2"),
)
# type equality. true.__type__ is Bool

# String() -> __str__
# number literals

# tuples, arrays

# // **

# int or float ** float
# float and float // -> int