storing variables

var a:Int
var a:Int = 2
var b:T = T(2)
...

the interpreter is not smart in how it evaluates the contents of the class. It goes statement by statement.
OOP languages usually allow the above to some degree.
The first implementation used the context's copy value
the only correct way to do it is to store the AST of the rvalue, and evaluate them all on object initialization.


### Class contents execute in a limited context
The original idea was to parse class content as a code black, add a scope level, execute it, then use it as its __fields__.
This freedom could help code generation. You could start writing inside a `{...` block inside the class, which means these variables would stop existing and not get written into the fields.
Inside this temporary scope, one could for example generate functions, and then simply do something like `this.__fields__[ID] = func` or `exec(repr(code), this)` to bind them

But some symbold need to be treated differently. Variables of the class written by simple `var x = 0` in its top level need to store the `0` as AST.

This is related to the dilemma where, if I wanted, I could provide such operators that the language's ability to form DSLs would explode.

`var x = 0` in the A class would become a call of `Class.__var__(A, [0 expr])`
`var x = 0` in the A class would become a call of `Class.__var__(A, [0 expr])`
`in x: code` would be `x.__scope__([code graph])`

This is because all the building blocks such as Class and Func are read-and-write objects of type Class, which by itself makes the modifiability unpredictable.

I do not like the __var__ idea.
It is not something I would ever use, and it seems to be a bad way to implement classes.
I starte

In all my code-generating code I have written, I do most 
95% - the langauge is enough
 4% - text generation
 1% - class patching
 
Text generation has to be separated. It will be useful! Repr and eval are.
But there's eg just no way to do
func {{ func_name }}
func (a_arg{{ ", _barg" if cond else "" }})

I cannot imagine how executable code could pass for an ID token of the func rule without the entire parsing engine going into crazy territory.
Same for the argument.

I remember thinking that maybe, arbitrary expressions could be accepted in a function's arguments. If it were null, it wouldn't be an argument at all.

 
With everything Twocode plans to do, I see
Cancelling executable code in the class level is the easiest solution.







With functions being objects, methods can be accessed and stored as well.

Can methods be treated like objects?
Are methods persistent?

The interpreter works quite well just evaluating the AST. A method call

a.f()

would be

(a.f)()

which means a.f has to return a BoundMethod, kind of a partial cast.

'''
>>> var f1 = a.f
var f2
f1 is f2
>>> a.f == a.f
'''

on request(may be stored)
__bounds__

## The loop
BoundMethod being an object and all methods being initialized into __bounds__ creates a loop if BoundMethod has any other methods, like __repr__.
The BoundMethod object needs to create a BoundMethod into its __bounds__ for the repr, which...

## The decision

BoundMethods can be objects.
You can still inspect them, see which method of which object it is.
Making BoundMethods not persistent makes only one thing impossible:

Using BoundMethods as keys, identified not even by their properties, but by their addresses.
Bad.



# func access from class and getattr
    # printing a class should jump to its type. having type.__repr__ breaks this
    # all references of uses, except super, refer to the top level of the class
    
    
    
    
    
    
    
    
    

```    
func type resolve fails on sources but name ref does not?
or type? type.ops?


decisions:
type creation is powerful enough that a syntax-transparent object might exist WITHOUT __getattr__
it is necessary for scope though
+ is equivalent to __add__
B.__add__ may return A.__add__
inhert_fields defined inheritance - this functions
__init__ and __new__ are of type
has scope, like func does. qualnames removed
methods can be callables
method building overwrites it, but the structure is not there by default
getattr of object cannot be how you implement interfaces. type_obj.__repr__ would then break it as a type object
getattr is for scopes, for a.b. a+ is equivalent to a.__type__.__add__
    and super simply refers to this.__type__.__base__
static - runtime interrupt


static func
method (this:T
var (macro)
callable

getter, setter - an artifical slot

var Slot()

a regular getter variable Slot(get=, set=)
static, getattr

__term__
but access scope really
__assign__
```

