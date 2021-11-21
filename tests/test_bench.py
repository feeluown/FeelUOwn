from feeluown.library import BriefSongModel
from feeluown.utils.utils import DedupList


def test_hash_model(benchmark, song):
    benchmark(hash, song)


def test_richcompare_model(benchmark, song):
    benchmark(song.__eq__, song)


def test_deduplist_addremove(benchmark):
    def addremove():
        song_list = DedupList()
        num = 1000
        for i in range(0, num):
            song = BriefSongModel(source='xxxx', identifier=str(i))
            if song not in song_list:
                song_list.append(song)
        for i in range(num // 10):
            song_list.pop(0)
    benchmark(addremove)
