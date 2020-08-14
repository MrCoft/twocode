from twocode import utils
import inspect
import os

def import_code_env():
    frame, filename, lineno, function, code_context, index = inspect.stack(0)[1]
    module = frame.f_globals

    transp = Transpiler.current
    context = transp.context
    module.update({"transp": transp})
    module.update(context.native_env)

    for name in "Func, Arg, Class, Attr, BoundMethod, Var".split(", "):
        module[name] = context.objects[name]

    op = utils.Object()
    def gen_op(name):
        native = context.operators[name].native
        op[name] = lambda *args, **kwargs: context.unwrap(native(*[context.wrap(item) for item in args], **{key: context.wrap(item) for key, item in kwargs.items()}))
    for name in "repr, qualname, eq, bool, string, hasattr, getattr, setattr, getitem, setitem, contains, eval".split(", "):
        gen_op(name)
    module["op"] = op

    for name in """
        Object, Null, \
        Bool, Float, Int, String, \
        List, Array, Tuple, \
        Map, Set, \
        Dynamic, \
    """.split(", "):
        name = name.strip()
        if name:
            module[name] = context.basic_types[name]

    for name in "ObjectScope, Module, Env".split(", "):
        module[name] = context.scope_types[name]
    # NOTE: Scope is shadowed
    #

class Transpiler:
    def __init__(self, context):
        self.context = context
        from .code_edit import CodeEdit
        self.code_edit = CodeEdit()
        Transpiler.current = self
    current = None

    def discover_classes(self, env=None):
        from .scope import discover_classes
        discover_classes(env)

    def map_code(self):
        from .scope import map_code
        map_code()

    def type(self):
        from .type_infer import TypeInfer
        type_infer = TypeInfer(self)
        type_infer.infer()
        type_infer.summary()

    def gen_source(self, lang):
        if lang == "python":
            from .targets.python import gen_source
        gen_source()

        #self.files = None
        #for type in self.all_types:
        #    print(type)

        # dirs = list in order  no, that's optim
        # files:
        # ["a/a.py"] = "text"

    def save(self, dir="."):
        for path, code in self.files.items(): # cd first? make dir first?
            path = os.path.join(dir, path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as file:
                file.write(code)

def transpile(context, *, lang, dir="."):
    transp = Transpiler(context)
    transp.discover_classes()
    transp.map_code()
    transp.type()

    transp.gen_source(lang)
    transp.save(dir)

# therefore:
# 1. we need complete typing
# 2. we need working decorators
# 3. we need working inlining

# example:
"""
@include("re") include(*args
class Regex:
    func push(item):
        native("self.append(item)")
"""
    # inline
    # a "static func wrapper impl" around basic type methods

    # type everything
    # find references to List.push
    # inline replace them:
    # game.units.push(item)
    # List.push(game.units, item)
    # native("")
        # some string that can be resolved in a const environment
        # const = literals and/or macros
        # "{}.append({})".format(self_term, args_code)

        # push(macro this, macro *args)
        # return native("{}.append({})".format(this.source(), args.source())

    # ->
    # game.units.append(item)

# 1. the func is macro/inline
# 2. it's a compiler step, which renames these calls using constants/transformations

# 4. can i implement these using native properly?
# 1. list push -> list.append




# 3. main, run, utils.cd, thourgh python -m
    # _box is weird
    # main is a static func

# currently, if you do not provide an arg for a func, it's not defined in the scope at all
# and can be resolved elsewhere if possible. huge bug.
"""
var x = 2
var f = x -> x
f(3)
f()
"""
# CODE_EDIT WORKS. REFACTOR THO
# SCOPE TRIGGERS, TYPING



# CONTEXT TREE, BETTER TABLE,
# ENV TREE
# indent more often, see python.py






    # context tree - that will be difficult
# refactor preview node, preview func

# revisit all old printing
# Env tree!

# Context Code Type Message
# Its Width!!!

"""
Game.ABC
 |____main()
  |
|
Game.main()
   |__

A.B.C
A.B.D
A.E

A.B
|_C
| |_G
| |_H
|_D
A.E


Game.ABC:
 main():


"""



# further than 12 lines away from last Game, write Game again
# what's the point of the three if you don't gain any chars because of indentation?


# scope, map_code -> outside



# 1. code edit

# triggers:
# scope, type_infer, analysis(pure, lvalue), validate (validators) validation

# what if i change an expr and add 4 statements before that and add 1 class into the same module?

# 2. modules
# 3. run it, use from within 2c
# 4. actual code editing - pure, lvalue, unique name, macro interpolation / code formatting









"""
const_macro


func const_macro(f):
    func wrapped(transform:Matrix4, macro *args, macro **kwargs):
        in __stack__[-1]:
            return f(transform, *args, **kwargs)


    takes some arguments as value (assumes they are literals)
    also can you use local literal values?

    OR: can you exec arbitrary code if it's in an isolated scope?


    var x
    in Scope():
        set x's value
    macro_call(x) -> i will attempt to calculate x now

"""

    # . copy()? how EXACTLY do you implement certain sweep features?
    # that need it to be typed, then replace it, then type it again?


# from within 2c:
# code.compiler.Transpiler
# or code.compiler.Compiler

# comp = Compiler()
# do the thing
# produce text

# comp.lang = "python"
# .compile()
# .run()

# compile(env, lang="python")
# run(env, lang="python")

if __name__ == "__main__":
    from twocode import Twocode
    context = Twocode()

    context.imp("Game")
    from twocode.transpiler import transpile
    transpile(context, lang="python", dir="src")
