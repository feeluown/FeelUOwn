import pytest
from unittest import mock, TestCase

from feeluown.utils.reader import RandomReader, RandomSequentialReader, wrap


def test_sequential_reader():

    def g_func():
        for i in range(0, 5):
            yield i

    g = g_func()
    reader = wrap(g)
    assert len(list(reader)) == 5


@pytest.mark.asyncio
async def test_async_sequential_reader():
    async def ag_func():
        for i in range(0, 5):
            yield i

    ag = ag_func()
    reader = wrap(ag)
    assert len([x async for x in reader]) == 5


class TestRandomReader(TestCase):
    # pylint: disable=protected-access

    def setUp(self):
        count = 105
        read_func = lambda start, end: list(range(start, end))  # noqa
        self.p = RandomReader(count, read_func=read_func, max_per_read=10)
        ranges = [(0, 20), (30, 45), (50, 60), (70, 95)]
        self.p._objects = [None] * count
        for r in ranges:
            self.p._objects[r[0]:r[1]-1] = list(range(r[0], r[1]))
        self.p._refresh_ranges()
        assert self.p._ranges == ranges

    def test_init_reader(self):
        with self.assertRaises(AssertionError):
            RandomReader(100, lambda: 1, 0)

    def test_read_range(self):
        mock_read_func = mock.MagicMock()
        mock_read_func.return_value = list(range(20, 30))
        self.p._read_func = mock_read_func

        self.p.read(30)
        obj = self.p.read(25)
        self.assertEqual(obj, 25)
        mock_read_func.assert_called_once_with(20, 30)

    def test_readall(self):
        mock_read_func = mock.MagicMock()
        self.p = RandomReader(102, read_func=mock_read_func, max_per_read=50)
        mock_read_func.side_effect = [list(range(0, 50)),
                                      list(range(50, 100)),
                                      list(range(100, 102))]
        objs = self.p.readall()
        self.assertEqual(len(objs), 102)
        self.assertEqual(objs[0], 0)
        mock_read_func.assert_has_calls([
            mock.call(0, 50),
            mock.call(50, 100),
            mock.call(100, 102),
        ])

    def test__has_index(self):
        yes, r = self.p._has_index(45)
        assert yes is False
        assert (45, 50) == r
        yes, r = self.p._has_index(10)
        assert yes is True
        assert (0, 20) == r

    def test__refresh_ranges(self):
        self.p._objects = [0, None, 0, None, 0, 0]
        self.p._refresh_ranges()
        self.assertEqual(self.p._ranges, [(0, 1), (2, 3), (4, 6)])

        self.p._objects = [0, 0, 0, 0, 0]
        self.p._refresh_ranges()
        self.assertEqual(self.p._ranges, [(0, 5)])

        self.p._objects = [None, None]
        self.p._refresh_ranges()
        self.assertEqual(self.p._ranges, [])

        self.p._objects = []
        self.p._refresh_ranges()
        self.assertEqual(self.p._ranges, [])


class TestRandomSequentialReader(TestCase):
    def test_usage(self):
        count = 11
        mock_read_func = mock.MagicMock()
        mock_read_func.side_effect = [list(range(0, 10)), list(range(10, 11))]
        reader = RandomSequentialReader(count,
                                        read_func=mock_read_func,
                                        max_per_read=10)
        value = next(reader)
        mock_read_func.assert_called_once_with(0, 10)
        self.assertEqual(value, 0)
        self.assertEqual(reader.offset, 1)
        for _ in range(1, 11):
            next(reader)
        mock_read_func.assert_has_calls([
            mock.call(0, 10),
            mock.call(10, 11),
        ])
        self.assertEqual(reader.offset, 11)
        with self.assertRaises(StopIteration):
            next(reader)
        self.assertEqual(reader.offset, 11)
