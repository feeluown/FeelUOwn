from unittest import TestCase

from fuocore.dispatch import Signal
from fuocore.dispatch import receiver

from .helpers import mock


class A(object):
    def f(self, *args, **kwargs):
        print('a.f called')


def f(*args, **kwargs):
    print('f called')


class SignalTest(TestCase):
    def setUp(self):
        self.a1 = A()
        self.a2 = A()

    def tearDown(self):
        pass

    def test_ref(self):
        s = Signal()
        self.assertTrue(s._ref(self.a1.f) == s._ref(self.a1.f))
        self.assertFalse(s._ref(self.a1.f) == s._ref(self.a2.f))

    def test_connect1(self):
        with mock.patch.object(A, 'f', return_value=None) as mock_method_f:
            s = Signal()
            # pay attention
            self.assertTrue(self.a1.f == self.a2.f == mock_method_f)
            s.connect(self.a1.f)
            s.emit(1, 'hello')
            mock_method_f.assert_called_once_with(1, 'hello')

    def test_connect2(self):
        s = Signal()
        s.connect(f)
        s.emit(1, 'hello')
        s.emit(1, 'hello')

    def test_disconnect(self):
        s = Signal()
        s.connect(f)
        s.disconnect(f)
        s.emit(1, 'hello')

    @mock.patch.object(Signal, 'connect')
    def test_receiver(self, mock_connect):
        s = Signal()

        @receiver(s)
        def f():
            pass
        self.assertTrue(mock_connect.called)
