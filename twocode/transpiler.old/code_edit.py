
class CodeEdit:
    def __init__(self):
        self.add_triggers = []
        self.remove_triggers = []
        # list of nodes, scopes of the subtree

    def add_node(self, node):
        pass
    def remove_node(self, node):
        pass
    def replace_node(self, parent, attr, node, index=None):
        old_node = getattr(parent, attr)
        if index is None:
            setattr(parent, attr, node)
        else:
            old_node = old_node[index]
            getattr(parent, attr)[index] = node
        self.remove_node(old_node)
        self.add_node(node)

        # what if i want to do a replacement?
        # remove_node(recursive=False) deep=False

        # say, with -> try + some statements
        # or provide a container of things that are already registered?
        # so that it stops at the old block

        # incremental api:
        # scope:
        # add_type (adds the type, creates scope)
        # map_code

        # new - add incrementaly an entire subtree
        # move, link -

        # or possibly - raw? old?
            # a node at which it does its job (so that it's linked correctly)
            # but does not continue

        def scope_add_node(node, *, parent):
            scope = transp.node_to_scope[parent]

            transp.all_nodes.append(node)
            transp.node_to_scope[node] = scope

            type_name = builtins.type(node).__name__
            code = None
            if type_name in "if_block for_loop while_loop with_block expr_block".split():
                code = node.block
            if type_name in "if_chain".split():
                code = node.else_block # wat
            if code:
                transp.all_codes.append(code)

            for child in node.children:
                if child is not code:
                    search_nodes(child, scope)
                else:
                    search_nodes(child, Scope(preview_node(node), parent=scope))

    def map_name(self, code, name, f, scope=None): # no f, *
        from . import import_code_env
        import_code_env()

        def map_code(enter=None, leave=None):
            def filter(node):
                if enter:
                    node = enter(node)
                scope = transp.node_to_scope[node]
                node.children = [(filter(child) if transp.node_to_scope[child] is scope else child) for child in node.children]
                if leave:
                    node = leave(node)
                return node
            return filter # more optimized

        def name_scopes(scope, name):
            scopes = []
            queue = [scope]
            while queue:
                scope = queue.pop(0)
                for child in scope.children:
                    if name not in child:
                        queue.append(child)
                scopes.append(scope)
            return scopes
            # order? var? nah

        def map_scopes(cond, enter=None, leave=None):
            def filter(node):
                scope = transp.node_to_scope[node]
                if not cond(scope):
                    return node
                if enter:
                    node = enter(node)
                node.children = [filter(child) for child in node.children]
                if leave:
                    node = leave(node)
                return node
            return filter

        if scope is None:
            scope = transp.node_to_scope[code]
        type_scope = scope
        return map_scopes(lambda scope: scope.find_name(name) is type_scope, leave=f)(code)








        # unique name, find all nodes with the name, change them

        # should i rename an attr though, i would have to rename all term_attr access of all nodes ever
        # that type to that
