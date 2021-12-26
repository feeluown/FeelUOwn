"""
This example proves the following experience (under multiple inheritance circumstances)

1. The `Base.initialize` method is only called once with `super().initialize()`
"""
class Base:
    def __init__(self):
        print('base init')

    def initialize(self):
        print('base initialize')

    def run(self):
        print('base run')


class Widget:
    def __init__(self, parent):
        print('widget init')


class A(Base):
    def __init__(self):
        super().__init__()
        print('A init')

    def initialize(self):
        super().initialize()
        print('a initialize')

    def run(self):
        super().run()
        print('a run')


class B(Base, Widget):
    def __init__(self):
        Base.__init__(self)
        Widget.__init__(self, self)
        print('B init')

    def initialize(self):
        super().initialize()
        print('b initialize')

    def run(self):
        super().run()
        print('b run')


class M(A, B):
    def __init__(self):
        super().__init__()

    def initialize(self):
        super().initialize()
        print('mixed initialize')

    def run(self):
        super().run()
        print('m run')


m = M()
m.initialize()
m.run()
