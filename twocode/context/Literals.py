literal_type = {
    "null": "Null",
    "boolean": "Bool",
    "integer": "Int",
    "float": "Float",
    "string": "String",
}
literal_eval = {
    "null": lambda value: None,
    "boolean": lambda value: value == "true",
    "integer": lambda value: int(value),
    "float": lambda value: float(value),
    "string": lambda value: value,
}
literal_wrap = {
    type(None): "Null",
    bool: "Bool",
    int: "Int",
    float: "Float",
    str: "String",
    list: "List",
    dict: "Map",
}