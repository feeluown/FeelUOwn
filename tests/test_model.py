from collections import namedtuple
from unittest import TestCase

from fuocore.models import Model, BaseModel, display_property


class FakeProvider:
    identifier = 'fake'
    name = 'fake'

    def set_model_cls(self, *args, **kwags):
        pass


provider = FakeProvider()


class TestModel(TestCase):

    def test_meta_class(self):

        class SongModel(Model):
            class Meta:
                provider = provider

        song = SongModel()
        self.assertEqual(song.meta.provider.name, 'fake')

    def test_meta_class_inherit(self):
        class SongModel(Model):
            class Meta:
                model_type = 1  # song model

        class LastSongModel(SongModel):
            pass

        song = LastSongModel()
        self.assertEqual(song.meta.model_type, 1)

    def test_meta_class_inherit_with_override(self):
        class SongModel(Model):
            class Meta:
                model_type = 1  # song model

        class LastSongModel(SongModel):
            class Meta:
                provider = provider

        song = LastSongModel()
        self.assertEqual(song.meta.model_type, 1)
        self.assertEqual(song.meta.provider.name, 'fake')


class TestBaseModel(TestCase):
    def test_display_fields(self):
        class SongModel(BaseModel):
            class Meta:
                fields = ['title', 'album']
                fields_display = ['album_name']

            @property
            def album_name(self):
                return self.album.name if self.album else ''

        album_name = 'Minutes-to-Midnight'
        song = SongModel.create_by_display(identifier=1, album_name=album_name)
        self.assertEqual(song.album_name_display, album_name)
        self.assertEqual(song.album_name, '')

        real_album_name = 'Minutes to Midnight'
        song.title = 'Leave out all the rest'
        Album = namedtuple('Album', ('name', ))
        song.album = Album(real_album_name)
        song.use_display = False
        self.assertEqual(song.album_name, real_album_name)


class TestDisplayProperty(TestCase):
    def test_display_basic_usage(self):
        class A:
            stage = 4
            a_display = display_property('a')

        a1 = A()
        a2 = A()
        self.assertEqual(a1.a_display, '')
        a2.a_display = 'a2'
        self.assertEqual(a1.a_display, '')
        self.assertEqual(a2.a_display, 'a2')
