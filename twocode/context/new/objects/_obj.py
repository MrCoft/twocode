
'''

    """
        DESIGN:
        e.g. boundmethod_repr wants to get the __type__ of its "obj" attribute
            before: this.obj.__type__
            after: this.obj.obj.obj.__type__
        because
            this.obj (the object behind the "this" ref) .obj (its obj attribute) .obj (the ref object) .__type__

        every native function definition would be filled with ".obj"s
        we can't unwrap the objects because the reftype matters, we often send it into the context's API
        assuming one would need to read these from the interpreter,
        all of the obj and ref attributes are accessible as internals

        the solution is to provide the same interface in Python that the internals do
        the reference is transparent, looks like the object,
        and its reference attributes can be accessed under __reftype__ and __refobj__


        NOTES:
        all objects passed around the interpreter are Refs
        context.obj.Object, Class etc. create Refs, it's rare to need to create an Object

        stored objects tend to be Objects:
            object attributes
            context.frame, context.get_env()
            class fields
            context Class and Func groups
            basic container types

    """



    w, uw, r, dr, op = [context.type_magic[name] for name in "w, uw, r, dr, op".split(", ")]

    native_wraps

    obj.Object, .Ref


    .objects, create,  classes
'''
