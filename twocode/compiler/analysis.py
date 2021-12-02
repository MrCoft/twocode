import ast


class CountNodeTypesVisitor(ast.NodeVisitor):
    def __init__(self):
        self.node_type_counts = {}

    def generic_visit(self, node: ast.AST):
        name = node.__class__.__name__
        self.node_type_counts.setdefault(name, 0)
        self.node_type_counts[name] += 1
        return super().generic_visit(node)


def print_node_type_counts(code):
    visitor = CountNodeTypesVisitor()
    visitor.visit(code)
    sorted_pairs = sorted(visitor.node_type_counts.items(),
                          key=lambda pair: pair[1], reverse=True)

    print()
    print('### Node type counts:')
    print()
    for (name, count) in sorted_pairs:
        print(f'{name:<15} {count}')
