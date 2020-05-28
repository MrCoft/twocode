from .testdefs import *

name_tests(
    # syntax
    syntax = cmp("func f(): {}"),
    syntax_args = cmp("func f(a, b:Int=2)->T: {}"),
    # format
    format_enter = cmp("func f():\n\t1\n\t2"),
    format_single = cmp("func f(): 1"),
    format_strip = cmp("func f(): {;0;}", "func f(): 0"),
    format_anon = cmp("func(): {}"),
    # stmt
    stmt = cmp("var f = func(): {}"),
    # arrow
    arrow_no_args = cmp("() -> 2", "func()->Dynamic: return 2"),
    arrow_single_arg = cmp("x -> 2", "func(x)->Dynamic: return 2"),
    arrow_parens = cmp("(x) -> 2", "func(x)->Dynamic: return 2"),
    arrow_multiple_args = cmp("(a, b) -> 2", "func(a, b)->Dynamic: return 2"),
    # arrow_sign=cmp"()",

    # ?, *, :T=val

    # arrow_sign=evals("(a:Int, b:Int) -> 0", "<func (Int,Int)->Dynamic>")




    pack_defaults = fails(),
    pack_opt = fails(),



    # macro
    macro_syntax = cmp("func(macro node): {}"),
    macro_optional = evals("((?macro node)->node)()", "null"),
    macro_default_null = evals("((macro node=null)->node)()", "null"),
    macro_decor = evals("@((macro node)->node) a + b", "macro a + b"),
    macro_pack = evals("((*macro args, **macro kwargs) -> args, kwargs)(a.b, key=c * d)", "(macro a.b, macro c * d)"), # prec, interaction with sent *args?




    macro_arg_type = fails("macro node:Type"),
    # wrong miss illegal error syntax
    macro_func_type = evals("Code->"),
    macro_func_repr = evals("without Code"),






    # pack
    pack_syntax = cmp("func(*args, **kwargs): {}"),
    pack_args_type = evals("((*args)->args)(1, 2)", "[1, 2]"),
    pack_kwargs_type = evals("((**kwargs)->kwargs)(key=2)", '["key": 2]'),

                     # *args:List<T>, conversion

    # optional
    optional_syntax = cmp("func(?x): {}"),
    optional_converts = evals("((?x)->x).args", '[Arg("x", default_=macro null)]'),
    optional_repr = evals("(func(?x): {}).source()", '"func(?x): {}"'),
    optional_default = fails("(?x=1)->x", "SyntaxError: optional argument with default value"),
    # object
    object_type = evals("(x->x).__type__", "<class Func>"),
    object_repr = evals("x->x", "<func Dynamic->Dynamic>"), #
    object_source = evals("(func(x): return x).source()", '"func(x): return x"'),
    object_source_bound = evals('(func(this:T): {}).source_bound(T, "call")', '"func call(): {}"'),
    object_code = evals("(x->x).code", "macro return x"),
    object_signature = evals("(x->x).signature()", '"(x)->Dynamic"'),
    # object_type = evals("(x->x).type()", '"Dynamic->Dynamic"'),



    # type
    type_map = evals("(func(obj:T)->T: {}).type()", '"T->T"'),
    type_script = evals("(func(): {}).type()", '"()->()"'),
    type_args = evals("(func(a:T, b:T)->T: {}).type()", '"(T,T)->T"'),



    object_return_type = evals("@qualname (func()->T: {}).return_type", '"T"'),


    sign_no_return = evals("(func(): {})"),
    # return_type of a thing that does not spec it

    # format, string
    # repr

    edit_repr = evals("func(a:Float, b:Float)->Float: {}", "<func (Float,Float)->Float>"),
    edit_code = evals("(x -> x + 2).code", "macro x + 2"),
    edit_args = evals("((a, b)->{}).args", '[Arg("a"), Arg("b")]'),
    edit_return_type = evals("(func()->Float:{}).return_type", "<class Float>"),

    arrow_id = evals("a->"),
    arrow_arg = evals("(x, y:Float=2)->"),
    arrow_tuple = fails("a,b->a"),

    complicated_arg = evals("(macro ?a:Float=2)->"),

























    # keyword
    keyword_only_syntax = cmp("func(*args, key, **kwargs): {}"),
    keyword_only_star = cmp("func(*, type): {}"),

    keyword_only_miss = evals("((*args, ?key)->key)(1)", "null"),
    keyword_only_pass = evals("((*args, ?key)->key)(key=1)", "1"),

    keyword_star_extra = fails("((*, ?key)->key)(1)"),
    # a char into *



    # sign
    # names
    mismatch_less = fails("(a->a)()"),
    mismatch_more = fails("(()->a)(1)"),
    mismatch_keyword = fails("((*, key)->2)()"),




    pack_keyword = evals("(x->x)(x=2)", "2"),


)
# >>> f()
# <Module object>
# TypeError: <lambda>() missing 1 required positional argument: 'x'


# positional, keyword works
        # unpack list, dict work
        # they do

        # * can bypass a macro arg
        # ** too

        # *2 items into macros?

# * accepts any iterable thing

# what are iterable things?
# actual list
# something that converts to a list?
# iterator
# iterable

# a thing that converts to a list is NOT an iterable
# but, if you want a list, and list has FROM iterable, and a thing has FROM list?

# sign tests





"""


func_type_str
>>> a -> b
<func Object->Object>
>>> func(x:Float)->Float: {}
<func Float->Float>



>>> ff(f)
<func ()->()>

<func Float->Float>


func f(macro node)
(macro node)->


"""



























"""

    # int? dunno
    # keyword-only
    keyword_only_syntax



    keyword_only_wrong = fails("((*, key=null)->key)(1)"),
    # all named after * are required to be keyword only


    # fails - func(*args, **kwargs, key): {}
    # fails - ()(2)

    # miss keyword
    pack = evals("((*args, **kwargs) -> args, kwargs)(0, a=1)", '[0], ["a": 1]'),
    keyword_arg = evals("((a, b) -> a, b)(0, b=1)", "(0, 1)"),
    unpack = evals("((a, b) -> a, b)(*[0], **Map(b=1))", "(0, 1)"),

    pack_multiple_args = fails("* *"),
    pack_multiple_kwargs = fails("** **"),

    keyword_only_after_kwargs = fails("**kwargs, key", "SyntaxError: invalid syntax"),
"""
# the "automacro" stuff... or evals? should be ().source()




# unpack_args
# pack_args
# term_call

# TypeError: <lambda>() missing 1 required keyword-only argument: 'key'
# if











# func f(a=2, b) is allowed! why not? test that







# to validators!

# can't @functools.wraps(f) before a lambda. can you in twocode?

# f(x, y, /) - no args

# create partial cast
# thats codebase shit

# precedence so we can safely a -> a + b