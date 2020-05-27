
r = 2
w = 3

def f():
    return k

def gen(i):
    def g():
        return i
    return g

# f.__code__.co_names = ('r',), read-only
# f.__globals__ = this module, read-only
# https://stupidpythonideas.blogspot.com/2015/12/how-lookup-works.html
# cell, ctypes.pythonapi, cell_contents

# for typing - global magics, typed, equal to None
    # need to test docs for that
# for perf - edit top-level funcs into class methods that pull out magics
# construct code, turn free var references into local references, add name pull out at the start, add arg
    # also resolve all mentions, we write other funcs as stateless also but turn them into methods

# classic di still maybe yes
    # + custom pipeline (eg signature sweep)
    # + nonlocal hacking

# what we did wrong:
# order not solved
# new instance of each method/class

# analyse which methods end up mutating state, omit passing elsewhere
# module registers utility scope, but we only import what func uses
# we silently add state to other context stuff we call?
# so it's written AS IF global but turned to class

# we do my tricks because it's difficult
# probably should be implementid as all monkey-patching, methods on a class
# do typing for editor, top-level for docs?
    # types are "import *"
# and then i hack everything i can and setup the interpreter somehow

# new idea - just write an interpreter generator, some jinja2 templates?
    # ah no support fk
