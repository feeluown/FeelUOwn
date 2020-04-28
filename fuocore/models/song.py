from fuocore.media import Quality, MultiQualityMixin
from fuocore.utils import elfhash
from .base import BaseModel, ModelType, _get_artists_name


class SongModel(BaseModel, MultiQualityMixin):
    QualityCls = Quality.Audio

    class Meta:
        model_type = ModelType.song.value
        fields = ['album', 'artists', 'lyric', 'comments', 'title', 'url',
                  'duration', 'mv', 'media']
        fields_display = ['title', 'artists_name', 'album_name', 'duration_ms']

        support_multi_quality = False

    @property
    def artists_name(self):
        return _get_artists_name(self.artists or [])

    @property
    def album_name(self):
        return self.album.name if self.album is not None else ''

    @property
    def duration_ms(self):
        if self.duration is not None:
            seconds = self.duration / 1000
            m, s = seconds / 60, seconds % 60
        else:
            m, s = 0, 0
        return '{:02}:{:02}'.format(int(m), int(s))

    @property
    def filename(self):
        return '{} - {}.mp3'.format(self.title, self.artists_name)

    def __str__(self):
        return 'fuo://{}/songs/{}'.format(self.source, self.identifier)  # noqa

    def __hash__(self):
        try:
            id_hash = int(self.identifier)
        except ValueError:
            id_hash = elfhash(self.identifier.encode())
        return id_hash * 1000 + id(type(self)) % 1000

    def __eq__(self, other):
        if not isinstance(other, SongModel):
            return False
        return all([other.source == self.source,
                    other.identifier == self.identifier])
