
    Scope.__fields__["__contains__"] = Func(native=lambda this, name: name in this.__this__)
    Scope.__fields__["__getitem__"] = Func(native=lambda this, name: this.__this__[name].value)

# func scopes look into this
# in_block rewrites this? this is top module? this can be written to?

    def imp(path):
        path = path.split(".")
        try:
            for i, name in enumerate(path[:-1]):
                if name in context.scope:
                    package = context.scope[name]
                else:
                    package = Module()
                    context.declare(name, package)
                context.stack.append(package)

                filepath = ".".join(path[:i+1])
                if not lookup(filepath):
                    raise ImportError("no package named {}".format(repr(name)))
                filename = lookup(filepath + ".__package__") # file?
                if filename:
                    ast = context.parse(open(filename, encoding="utf-8").read())
                    context.eval(ast)

            # wrong package/module split
            # last might be any

            # only last part declared here
            # top level in top level - including explicit names
            # explicit names return the thing
            name = path[-1]
            if name in context.scope:
                module = context.scope[name]
                context.stack.append(module)
            else:
                module = Module()
                context.declare(name, module)
                context.stack.append(module)
                filename = lookup(".".join(path))
                if not filename:
                    raise ImportError("no module named {}".format(repr(name)))
                ast = context.parse(open(filename, encoding="utf-8").read())
                context.eval(ast)
        finally:
            for i in range(len(path)):
                # error when?
                context.stack.pop()
        return module

    context.imp = imp






# normal
value = context.eval(value)
context.scope[node.id] = value
return value

# attempt from scope
id = node.id
if id in context.scope:
    return context.scope[id]

# attempt from this
if "this" in context.scope:
    this = context.scope["this"]
try:
    return context.getattr(this, id)
except AttributeError:
    pass




# import as




# old_scope = context.swap_stack(func.scope)

# whats the point of importing?

# a func that prints a path to a type in the current context - full path if imported, else
    # in func repr


# how different is it?




    # some builtin property


# end with a .T attempts to set it to T.T, or returns that - nat crossroad

# a.b, a[b], in a: var x:T
# a func that sets it using a type
# class wrappers


# the split of all those things crammed into the basic scope
# eg where are Class etc. a package? code.types?

class ExprGraph:
    var graph:Code
    var term:Term


class TermStack:
    var terms:List<Term>

    func __getattr__(name:String):
        for term in terms:

    func __expr__():
        return terms[-1]