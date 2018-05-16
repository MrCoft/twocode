from twocode.parser.indent_parser import IndentParser
from twocode.parser import Context as ParserContext

class Parser(ParserContext):
    def __init__(self):
        from .grammar import lexer, grammar
        super().__init__(lexer(), grammar())

        from .grammar import transform_types, map_literals, prec
        node_types = self.node_types
        node_types, transform = transform_types(node_types)
        self.node_types = node_types
        m_literals = map_literals(self)
        #node_types, t_int = transform_int(node_types)
        #node_types, t_op_prec = transform_op_prec(node_types)
        self.transforms += [
            transform,
            m_literals,
        ]

        parser = IndentParser()
        from twocode.parser.state_parser import Parser as StateParser
        parser.parser = StateParser(self.rules)
        from twocode.parser.indent_parser import gen_valid_indent, gen_insert
        parser.valids.append(gen_valid_indent())
        parser.valids.append(prec(self.rules))
        parser.wrap_code, parser.insert = gen_insert(self.rules)
        self.parser = parser
        self.incr_parser = parser.parser
