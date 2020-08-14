from twocode.context.new.setup import attach


@attach('Class', '__init__', sign='(this:Class)')
def class_init(this):
    this.__fields__ = {}
    this.__base__ = None
    this.__frame__ = None
