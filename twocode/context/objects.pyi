from typing import Callable


class Ref:
    __refobj__: Object
    __reftype__: object

class Object:
    __type__: object
    __type_params__: object

class ContextObj:
    obj: Callable[['Type'], Object]
