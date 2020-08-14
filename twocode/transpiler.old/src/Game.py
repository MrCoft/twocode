
class ABC:

    def main(self):
        game = Game()
        for i in [5, 10, 20]:
            unit = Unit()
            unit.pos = Float2(i, i)
            unit.vel = Float2(-1, -2)
            game.units.append(unit)
        game.map = Map(12, 8)
        for i in [0, 1, 2, 3, 4, 5, 6]:
            game.update()
            print('frame:', i)
            for unit in game.units:
                print('unit:', unit.pos.x, unit.pos.y)

class Float2:
    def __init__(self, x=None, y=None):
        if x == None:
            x = 0.0
        if y == None:
            y = 0.0
        self.x = None
        self.y = None
        self.x = x
        self.y = y

    def __add__(self, vec):
        return Float2(self.x + vec.x, self.y + vec.y)
    def __mul__(self, r):
        return Float2(self.x * r, self.y * r)

class Game:
    def __init__(self):
        self.map = None
        self.physics = Physics()
        self.units = []
        self.physics.bodies = self.units

    def update(self):
        self.physics.resolve()
        for unit in self.units:
            if unit.pos.x < 0:
                unit.pos.x = -unit.pos.x
                unit.vel.x = -unit.vel.x
            if unit.pos.y < 0:
                unit.pos.y = -unit.pos.y
                unit.vel.y = -unit.vel.y

class Map:
    def __init__(self, width, height):
        self.grid = None
        self.height = None
        self.width = None
        self.width = width
        self.height = height
        self.grid = [width * height]

class Physics:
    def __init__(self):
        self.bodies = None

    def resolve(self):
        for body in self.bodies:
            body.pos = body.pos + body.vel

class Unit:
    def __init__(self):
        self.pos = Float2()
        self.vel = Float2()
