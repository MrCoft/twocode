some lang
evaluate to value
, which means-

put any code constuct anywhere


### Not everything is an expression
Some languages evaluate statements to values which means you can put any code construct anywhere.
This is largely related to how Python solves this problem by introducing extra syntax.

Examples:
```
// assignment chains
x = y = 2

// list comprehension
// statement
var x = [for i in 0...5: i]
// extra syntax
var x = [i for i in 0...5]
```


### Cons

### Pros


:

### Haxe
`return switch {}`

### Python
no `a = b = c`

setter operators need not return

Operators for `a[b] = c`, `a += b` need mostly useless returns.




H
multi-stmt []
return switch {}
a -> { ; }

P
no f(a=2)


### The best of both worlds





This fits everything I want it to do, losing one consistency.
Not all statements evaluate to expressions.
This works because any block you would want to evaluate ends with something like `a` or `a + 1` and never `var a = 2`.



ops don't return (eg a =2), a=b=c not working
blocks evaluate to last stmt
disable a=2 in arg
H syntax ( if a: b else: c

    




### Statements to expressions
Some of these decisions were influenced to Jupyter Notebook

Anonymous class and function definitions make sense to return.
It is also weird to see [null, null, ...] when ending a cell with a for loop.








# Iterators comprehension

Pretty, readable, makes the code shorter by turning the most common operation into a one-liner.
I like these two syntax forms:

### Python
```
[i for i in 0...5]
```
* Reads better, maybe. In most cases the right part can be considered the boring part and we only care about the expression, one wouldn't have to travel to the edge of the screen to read it.
* Allows simple stacking of the iterators.

### Haxe
```
[for i in 0...5: i]
```
* Does not require additional grammar rules. `for i in 0...5: i` could evaluate to same value.
* Multiple `:` block starts on the same line are dangerous, possibly invalid.











Examples:
```
// passing a value as determined by a condition
cond ? a : b
a if cond else b
// stmt
f(if cond: a else b)




```

The decision is between extra syntax or letting statements be expressions.

Not having to expand syntax is tempting. Not for the implementation, but for users.
I would never write a complicated assignment chain.
Most solution involving statements currently use the `:` token, which might require awkward grouping.

Right now statements are expressions, the code works that way. This might change.

__add__ should return a value, setindex, setattr etc should not
















{} if {} else {}
{} for {} in {}
{} while {}

_inline

    # [i for i in 0...10]
    # var a = (i for i in 0...10)
    
        AS literaly serves the purpose of it having a value
    it's either - {} for returns a value while for {} doesn't, or there's the eval(inline=) attribute
    
for _ does not print as a statement


iterators returning values are completely ok
syntax exceptions:
    (generator)
    [list compr]
    iter_compr
right now, map compr is impossible

allowing iter_compr chain would mean a single "map_item iter_compr_hain" rule would allow that
but it betrays normal for loops, which really do work

how?
eval(inline)
    code sets inline true for last thing
code, if, for, while
or stmt
    change how term expr stmt work
    
or generator