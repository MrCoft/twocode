
def test_context():
    import twocode.context.new
    import twocode.context.new.objects
    import twocode.context.new.objects.object
    import twocode.context.new.objects.ref
    import twocode.context.new as _c
    print(_c.objects.getattr, _c.objects.get_internals)

