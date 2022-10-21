import ast


class OpsToFuncsVisitor(ast.NodeTransformer):
    def visit_If(self, node):
        return ast.If(
            test=ast.Call(
                func=ast.Name(id='bool', ctx=ast.Load()),
                args=[self.visit(node.test)],
                keywords=[]
            ),
            body=[self.visit(stmt) for stmt in node.body],
            orelse=[self.visit(stmt) for stmt in node.orelse],
        )


def ops_to_funcs(code):
    visitor = OpsToFuncsVisitor()
    copy = visitor.visit(code)
    return copy

# __add__ etc
# for loop implicit iterator conversion
