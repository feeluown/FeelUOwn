from unittest import mock, TestCase

from fuocore.reader import RandomReader, RandomSequentialReader


class TestReader(TestCase):
    # pylint: disable=protected-access

    def setUp(self):
        count = 105
        read_func = lambda start, end: list(range(start, end))
        self.p = RandomReader(count, read_func=read_func, max_per_read=10)
        ranges = [(0, 20), (30, 45), (50, 60), (70, 95)]
        self.p._objects = [None] * count
        for r in ranges:
            self.p._objects[r[0]:r[1]-1] = list(range(r[0], r[1]))
        self.p._refresh_ranges()
        assert self.p._ranges == ranges

    def test_usage(self):
        mock_read_func = mock.MagicMock()
        mock_read_func.return_value = list(range(20, 30))
        self.p._read_func = mock_read_func

        obj = self.p.read(30)
        obj = self.p.read(25)
        self.assertEqual(obj, 25)
        mock_read_func.assert_called_once_with(20, 30)

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
        mock_read_func.return_value = list(range(0, 10))
        reader = RandomSequentialReader(count,
                                        read_func=mock_read_func,
                                        max_per_read=10)
        self.assertTrue(reader.allow_sequential_read)
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
