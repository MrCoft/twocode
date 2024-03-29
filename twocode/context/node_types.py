import builtins
from twocode import utils

def add_node_types(context):
    Object, Class, Attr, Func, Arg = [context.obj[name] for name in "Object, Class, Attr, Func, Arg".split(", ")]
    String, List, Bool = [context.basic_types[name] for name in "String, List, Bool".split(", ")]
    w, uw, r, dr = [context.type_magic[name] for name in "w, uw, r, dr".split(", ")]
    wraps = context.native_wraps

    node_types = context.parser.node_types

    context.node_types = utils.Object()
    def gen_class(name):
        cls = Class()
        context.node_types[name] = cls
        return cls
    def attach(cls, name, **kwargs):
        def wrap(func):
            cls.__fields__[name] = Func(native=func, **kwargs)
        return wrap

    def node_init(this, *args, **kwargs):
        type_name = type_to_name[this.__type__]
        node_type = node_types[type_name]
        for var, arg in zip(node_type.vars, args):
            setattr(this, var.name, arg)
        for key, value in kwargs.items():
            setattr(this, key, value)
    @wraps(result=True)
    def node_get_children(this):
        type_name = type_to_name[this.__type__]
        children = []
        for var in node_types[type_name].vars:
            child = uw@ getattr(this, var.name)
            if var.type and child:
                if not var.list:
                    children.append(child)
                else:
                    children.extend(child)
        return children
    @wraps("children")
    def node_set_children(this, children):
        children = iter(children)
        type_name = type_to_name[this.__type__]
        for var in node_types[type_name].vars:
            child = uw@ getattr(this, var.name)
            if var.type and child:
                if not var.list:
                    setattr(this, var.name, next(children))
                else:
                    list_var = []
                    for i in range(len(child)):
                        list_var.append(next(children))
                    setattr(this, var.name, w@ list_var)
    @wraps(result=True)
    def node_source(node):
        return str(context.unwrap_code(node))
    @wraps(result=True)
    def node_tree(node):
        return tree_str(context.unwrap_code(node))
    def tree_str(node):
        node_type = builtins.type(node)
        type_name = node_type.__name__
        if type_name not in node_types:
            return str(node)
        return node.str_func(delim=".\t".replace("\t", " " * (4 - 1)), str=tree_str)

    type_to_name = {}

    for type_name, node_type in node_types.items():
        cls = gen_class(type_name)
        cls.__fields__["__init__"] = Func(native=node_init)
        cls.__fields__["get_children"] = Func(native=node_get_children, args=[Arg("this", cls)], return_type=List)
        cls.__fields__["set_children"] = Func(native=node_set_children, args=[Arg("this", cls), Arg("children", List)], return_type=List)
        cls.__fields__["source"] = Func(native=node_source, args=[Arg("node", cls)], return_type=String)
        cls.__fields__["tree"] = Func(native=node_tree, args=[Arg("node", cls)], return_type=String)
        # NOTE:
        # chooses to require String
        # better than including node types in temp scope, they aren't used anywhere else
        type_to_name[cls] = type_name

    Code = context.node_types["code"]
    classes = "Term Expr Tuple Stmt Type".split()
    for class_name in classes:
        gen_class(class_name)
    # all extend Node? a data one

    code_from_map = {
        "Stmt": lambda node: node_types["code"]([node]),
        "Tuple": lambda node: node_types["code"]([node_types["stmt_tuple"](node)]),
        "Expr": lambda node: node_types["code"]([node_types["stmt_tuple"](node_types["tuple_expr"](node))]),
        "Term": lambda node: node_types["code"]([node_types["stmt_tuple"](node_types["tuple_expr"](node_types["expr_term"](node)))]),
    }
    class_from_map = {
        "Stmt": lambda node: node.lines[0],
        "Tuple": lambda node: node.lines[0].tuple,
        "Expr": lambda node: node.lines[0].tuple.expr,
        "Term": lambda node: node.lines[0].tuple.expr.term,
    }
    @attach(Code, "__from__", sign="(node:Object)->Code")
    def code_from(node):
        for class_name, map in code_from_map.items():
            cls = context.node_types[class_name]
            if context.extends(node.__type__, cls):
                return context.wrap_code(map(context.unwrap_code(node)))
        raise context.exc.ConversionError()
    def gen_class_from(class_name, map):
        cls = context.node_types[class_name]
        cls.__fields__["__from__"] = Func(native=lambda code: context.wrap_code(map(context.unwrap_code(code))), args=[Arg("code", Code)], return_type=cls)
    for class_name, map in class_from_map.items():
        gen_class_from(class_name, map)

    var_type_map = {var: String for var in "id op affix value type pack source path".split()}
    var_type_map["macro"] = Bool
    for type_name, node_type in node_types.items():
        cls = context.node_types[type_name]
        for class_name in classes:
            if type_name.startswith(class_name.lower()):
                cls.__base__ = context.node_types[class_name]
        args = cls.__fields__["__init__"].args
        args.append(Arg("this", cls))
        for var in node_type.vars:
            attr = Attr()
            arg = Arg(var.name)
            if var.type:
                if var.type.capitalize() in classes:
                    attr.type = context.node_types[var.type.capitalize()]
                if var.type in node_types:
                    attr.type = context.node_types[var.type]
            else:
                if var.name in var_type_map:
                    attr.type = var_type_map[var.name]
            if var.list:
                attr.type = List
                attr.default_ = context.parse("[]") # symbol = expr?
                arg.default_ = context.parse("[]")
            cls.__fields__[var.name] = attr
            arg.type = attr.type
            args.append(arg)

    def wrap_code(node):
        node_type = builtins.type(node)
        type_name = node_type.__name__
        if type_name not in node_types:
            return w@ node
        cls = context.node_types[type_name]

        obj = Object(cls)
        for var in node_type.vars:
            if not var.list:
                setattr(obj, var.name, context.wrap_code(node.__dict__[var.name]))
            else:
                setattr(obj, var.name, w@ [context.wrap_code(sub_child).__refobj__ for sub_child in node.__dict__[var.name]])
        return obj
    context.wrap_code = wrap_code

    def unwrap_code(node):
        type_name = type_to_name.get(getattr(node, "__type__", None))
        if type_name not in node_types:
            return uw@ node
        node_type = node_types[type_name]

        obj = object.__new__(node_type)
        for var in node_type.vars:
            if not var.list:
                setattr(obj, var.name, context.unwrap_code(r@ node.__dict__[var.name]))
            else:
                setattr(obj, var.name, [context.unwrap_code(r@ sub_child) for sub_child in uw@ node.__dict__[var.name]])
        return obj
    context.unwrap_code = unwrap_code

    StmtValue = gen_class("StmtValue")
    @attach(StmtValue, "__term__", sign="(this:StmtValue)->Object")
    def stmtvalue_term(this):
        return this.__this__
    @attach(StmtValue, "__expr__", sign="(this:StmtValue)->Object")
    def stmtvalue_expr(this):
        return this.__this__
    @attach(StmtValue, "__stmt__", sign="(this:StmtValue)->Null")
    def stmtvalue_stmt(this):
        return w@ None
    context.stmt_value = lambda value: Object(StmtValue, __this__=value)
