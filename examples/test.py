import ast

class Cls:
    def __init__(self):
        self.x = 2

    def method(self):
        print("Printing", self.x)

Cls.__2c_source__ = ast.parse('''
class Cls:
    def __init__(self):
        self.x = 2

    def method(self):
        print("Printing", 25)
''')

cls = Cls()
print('tst', dir(cls.__class__))
cls.method()
Cls.__2c_source__ = ast.parse('''
class Cls:
    def __init__(self):
        self.x = 2

    def method(self):
        print("Printing", 30)
    
    def method2(self):
        print("Printing", 30)
''')
# cls = Cls()
cls.method()
print('tst', dir(cls.__class__))

print(cls.__class__)
