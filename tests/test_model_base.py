from fuocore.models import Model as Struct


def test_basic_usage():
    class User(Struct):
        class Meta:
            fields = ['name', 'age']

    user = User(name='Tom', age=10)
    assert user.name == 'Tom'
    assert user.age == 10


def test_inherit_usage():
    class Lang(Struct):
        class Meta:
            fields = ['name']

    class Python(Lang):
        class Meta:
            fields = ['author']

    assert 'name' in Python._meta.fields
    p = Python(name='Python', author='Guido')
    assert p.author == 'Guido'
    assert p.name == 'Python'


def test_init_with_obj():
    class User(Struct):
        class Meta:
            fields = ['name']

    u1 = User(name='haha')
    u2 = User(u1)
    assert u2.name == 'haha'


def test_customize_init():
    class User(Struct):
        class Meta:
            fields = ['name']

        def __init__(self, **kwargs):
            super(User, self).__init__(**kwargs)

    class VIP(User):
        class Meta:
            fields = ['level']

        def __init__(self, **kwargs):
            super(VIP, self).__init__(**kwargs)

    u = VIP(name='haha', level=1)
    assert u.name == 'haha'


def test_customize_init_2():
    class User(Struct):
        class Meta:
            fields = ['name', 'age']

        def __init__(self, name, **kwargs):
            super(User, self).__init__(name=name, **kwargs)

    user = User(name='hello', age=10)
    assert user.name == 'hello'
    assert user.age == 10


def test_mix():
    class User(Struct):
        class Meta:
            fields = ['name', 'age', 'birthday']

    user = User(name='lucy', age=20, birthday='2017')

    class VIP(User):
        class Meta:
            fields = ['level']

    vip = VIP(user, level=1)
    vip2 = VIP(name='ysw', level=1)

    assert vip.name == 'lucy'
    assert vip.level == 1
    assert vip2.name == 'ysw'
    assert vip2.level == 1
    assert vip2.age is None


def test_mixins():
    class User(Struct):
        class Meta:
            fields = ['name', 'age', 'birthday']

    class Hacker(Struct):
        class Meta:
            fields = ['alias']

    class Student(User, Hacker):
        pass

    s = Student(name='ysw', alias='cosven')
    assert s.name == 'ysw'
    assert s.alias == 'cosven'


def test_init_with_part_kwargs():
    class User(Struct):
        class Meta:
            fields = ['name', 'age', 'birthday']

    u = User(name='ysw')
    assert u.age is None
