### Map, set literals

Maps comprise 20% of all variables in my scripts and 1% of all variables in my engine.
Set or a container, a `Map<T,[dummy]>`, is a type I use rarely. List is a container as well, making set mostly an optimization type.

In Python, the `{}` and `{"a": 0}` literals are consistent in that they are both unordered.
We can't use `{}` as-is because it is an empty code block and any set would be a single tuple-statement.

Creating sets easily is still possible, it could be e.g. a macro decorator `@set [1, 2]`.
I see set as unimportant. The language already provides a way to list items, which is the list literal.



3
`Map(**kwargs)` could replace the literal. Or this dirty macro:
```
@map_lines {
    a = 0
    b = 1
}
```

`map_lines` could parse a code block, allowing only assignments.
Both of these are limited in that they need string keys.
3



**There is no `{}` consistency
We are not doing `{1, 2}`, list is enough
Maps use square brackets: `["a": 0]`**






### Map comprehension
The crux is that map comprehension with the value on the right side looks horrible.
Even if we took Python, which does it well, and this was the only change we made:
```
{for key, value in obj.items(): key: value}
```
The `a: b: c` end is bad.

### Alternatives
We could go without a map literal
It's possible to design a macro to help write map comprehension:
```
[for key, value in obj.items(): key, value]
[for key, value in obj.items(): key->value]
[for key, value in obj.items(): key = value]
```
Arrow function and assignment limit the key to an id


Twocode diverges from Python's syntax in its use of {} blocks, [] maps and evaluated-statement comprehensions.

Python



[for a in b: c: d]
[c: d for a in b]
[for a in (b: c): d]

[for a in b: c, d]
[for a in b: c->d]
[for a in b: c -> d]

[for name, value in scope.items():    name: context.wrap(value)]

solution:

even if we took python, which does it well, and this was the only change we made
-> left-side compr

a: b allows exponential parsing combinations
solution:
[key: value for key, value in obj.items()] is a special case
this creates an inconsistency that this language has been trying to avoid
    don't create weird one-statement limitations in the syntax
    python does it in comprehensions and lambdas
    twocode walks around that using curly brace blocks
but, allowing a: b in curly braces to evaluate leaves us with the vulnerability
not if we make it a statement

also, ideally, these translate to a normal for loop, the interpreter catches this,
    and ideally it repr's back
one possible inconsistency is that waiting for the evaluator to return a mapping
    might create a list instead, when the iterator is empty

@Map.literal    or compr
@Set
    @map @set

    the left side defends against this using...?


saying the "core of this language" is so that i can correctly type a list/map/set using a comprehension
    without once typing it? no @map, no :Map = ?
    start writing translatable code and get over yourself, interpreter