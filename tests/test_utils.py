import pytest
from copy import copy, deepcopy
from feeluown.utils.utils import DedupList


class Obj:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self, other):
        return self.value


def test_dedup_list():
    # init
    assert DedupList([1, 2, 3]) == [1, 2, 3]
    dlist = DedupList([3, 2, 3, 4, 2, 3, 1])
    assert dlist == [3, 2, 4, 1]

    # add
    dlist = dlist + [5, 1, 6]
    assert isinstance(dlist, DedupList)
    assert dlist == [3, 2, 4, 1, 5, 6]

    # radd
    dlist = [1, 2, 3, 7] + dlist
    assert isinstance(dlist, DedupList)
    assert dlist == [1, 2, 3, 7, 4, 5, 6]

    # setitem
    dlist[0] = 8
    assert dlist == [8, 2, 3, 7, 4, 5, 6]
    with pytest.raises(ValueError):
        dlist[2] = 5

    # append
    dlist.append(8)
    assert dlist == [8, 2, 3, 7, 4, 5, 6]
    dlist.append(9)
    assert dlist == [8, 2, 3, 7, 4, 5, 6, 9]

    # extend
    dlist.extend([8, 1, 10, 11, 3])
    assert dlist == [8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 11]

    # insert
    dlist.insert(0, 5)
    assert dlist == [8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 11]
    dlist.insert(0, 12)
    assert dlist == [12, 8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 11]
    dlist.insert(-1, 13)
    assert dlist == [12, 8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 13, 11]
    dlist.insert(-12, 14)
    assert dlist == [12, 14, 8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 13, 11]
    dlist.insert(-14, 15)
    assert dlist == [15, 12, 14, 8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 13, 11]
    dlist.insert(-99, 16)
    assert dlist == [16, 15, 12, 14, 8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 13, 11]
    dlist.insert(99, 17)
    assert dlist == [16, 15, 12, 14, 8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 13, 11, 17]

    # pop
    assert dlist.pop() == 17
    assert dlist == [16, 15, 12, 14, 8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 13, 11]
    assert dlist.pop(0) == 16
    assert dlist == [15, 12, 14, 8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 13, 11]
    assert dlist.pop(-2) == 13
    assert dlist == [15, 12, 14, 8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 11]
    with pytest.raises(IndexError):
        dlist.pop(20)

    # copy
    dlist_orig = [Obj(i) for i in range(5)]
    dlist_copy = copy(dlist_orig)
    assert dlist_copy == dlist_orig
    assert id(dlist_copy) != id(dlist_orig)
    assert id(dlist_copy[0]) == id(dlist_orig[0])

    # deepcopy
    dlist_orig = [Obj(i) for i in range(5)]
    dlist_copy = deepcopy(dlist_orig)
    assert dlist_copy == dlist_orig
    assert id(dlist_copy) != id(dlist_orig)
    assert id(dlist_copy[0]) != id(dlist_orig[0])

    # getitem
    assert [dlist[i] for i in range(14)] == \
           [15, 12, 14, 8, 2, 3, 7, 4, 5, 6, 9, 1, 10, 11]

    # swap
    dlist.swap(7, 9)
    assert dlist == [15, 12, 14, 8, 2, 3, 7, 6, 5, 4, 9, 1, 10, 11]

    # index
    for idx, item in zip(range(len(dlist)), dlist):
        assert dlist.index(item) == idx
    with pytest.raises(ValueError):
        dlist.index(8, 4)
    with pytest.raises(ValueError):
        dlist.index(8, 1, 3)

    # sort
    dlist.sort()
    assert dlist == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15]
    for idx, item in zip(range(len(dlist)), dlist):
        assert dlist.index(item) == idx

    # remove
    dlist.remove(3)
    assert dlist == [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15]
    with pytest.raises(ValueError):
        dlist.remove(16)
    # index should be correct after item is removed
    assert dlist.index(1) == 0
    assert dlist.index(4) == 2

    # clear
    dlist.clear()
    assert dlist == []
