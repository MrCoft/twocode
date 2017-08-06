literal_eval = {
    "null": lambda value: None,
    "boolean": lambda value: value == "true",
    "integer": lambda value: int(value),
    "float": lambda value: float(value),
    "hexadecimal": lambda value: int(value, 16),
    "octal": lambda value: int(value, 8),
    "binary": lambda value: int(value, 2),
    "string": lambda value: value,
    "longstring": lambda value: value,
}
literal_wrap = {
    type(None): "Null",
    bool: "Bool",
    int: "Int",
    float: "Float",
    str: "String",
    list: "List",
    dict: "Map",
    tuple: "List",
}