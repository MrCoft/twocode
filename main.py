from twocode.compiler.twocode import Twocode

if __name__ == '__main__':
    context = Twocode()
    context.transform_script('examples/test.py')

    exit()

    # print(ast.unparse(code))
    exec(compile(code, 'test.py', 'exec'))
    # print(ast.dump(compile(text, 'test.py', mode='exec', ), indent=4))

    print(inspect.getsource(json.dumps))
    code = ast.parse(inspect.getsource(json.dumps), mode='exec')
    print(ast.dump(code, indent=4))

    print(json.dumps('{ "x": 2 }'))
    context = dict()
    exec(compile(code, 'test.py', 'exec'), context)
    print(context.keys())
    context['dumps']('{ "x": 2 }')
