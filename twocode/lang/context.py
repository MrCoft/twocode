class Twocode:
    def __init__(self):
        """
            SELF-ASSEMBLY PROBLEM:
            functions without signatures aren't inherited and can't be called
            but the best way to set a signature is to transplant it
            from a function you get from eval(parse(sign))
            but that needs scope with signed methods to work

            OLD DEPENDENCY HELL:
            caused by accessing objects that are introduced later

            objects require Code
            basic types define hash, needed by scope creation
            node_types have trouble looking up their names
            scope creation requires other types
            sign requires basics and scope
            scope_types requires typed hashes

            scope methods signed manually for sign to work:
            __init__ of Scope, Module, Env
            __getattr__ of Scope, Module
            declare of Scope, Module

            the tangle would be weaker if untyped signatures worked
            setup.flush_typing() when they don't
        """

        from .parser import Parser
        self.parser = Parser()
        self.parse = self.parser.parse

        from twocode.context.core import add_core
        add_core(self)
        from twocode.context.core import add_exceptions
        add_exceptions(self)
        from twocode.context.eval import add_eval
        add_eval(self)
        from twocode.context.setup import add_setup
        add_setup(self)
        from twocode.context.scope import scope_builtins
        scope_builtins(self)

        from twocode.context.objects import add_objects
        add_objects(self) # NOTE: required by everything else
        from twocode.context.basic_types import add_basics
        add_basics(self)
        from twocode.context.operators import add_operators
        add_operators(self)
        from twocode.context.builtins import add_builtins
        add_builtins(self)
        from twocode.context.node_types import add_node_types
        add_node_types(self)
        from twocode.context.scope import add_scope
        add_scope(self)
        from twocode.context.exceptions import add_exceptions
        add_exceptions(self)
        from twocode.context.typing import add_typing
        add_typing(self)
        from twocode.context.logging import add_logging
        add_logging(self)

        from twocode.context.scope import init_scope
        init_scope(self)
        from twocode.context.scope import scope_types
        scope_types(self)
        from twocode.context.scope import add_ref
        add_ref(self)
        # self.setup.end()

        import sys
        sys.setrecursionlimit(100000)
