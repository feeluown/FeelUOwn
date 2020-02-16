from fuocore.models import SongModel, ArtistModel, \
    AlbumModel, PlaylistModel, UserModel


simple_fields = set({'title', 'duration', 'url',
                     'name', 'artists_name', 'album_name'})


class ModelSerializerMixin:

    def _get_items(self, model):
        # initialize fields that need to be serialized
        # if as_line option is set, we always use fields_display
        if self.options['as_line'] or self.options['brief']:
            fields = model.meta.fields_display
        else:
            fields = self._declared_fields
        items = [("provider", model.source),
                 ("identifier", model.identifier),
                 ("uri", str(model))]
        if self.options['fetch']:
            for field in fields:
                items.append((field, getattr(model, field)))
        else:
            for field in fields:
                items.append((field, getattr(model, field + '_display')))
        return items


class SongSerializerMixin:
    class Meta:
        types = (SongModel, )
        # since url can be too long, we put it at last
        fields = ('title', 'duration', 'album', 'artists', 'url')
        line_fmt = '{uri:{uri_length}}\t# {title:_18} - {artists_name:_20}'


class ArtistSerializerMixin:
    class Meta:
        types = (ArtistModel, )
        fields = ('name', 'songs')
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'


class AlbumSerializerMixin:
    class Meta:
        types = (AlbumModel, )
        fields = ('name', 'artists', 'songs')
        line_fmt = '{uri:{uri_length}}\t# {name:_18} - {artists_name:_20}'


class PlaylistSerializerMixin:
    class Meta:
        types = (PlaylistModel, )
        fields = ('name', )
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'


class UserSerializerMixin:
    class Meta:
        types = (UserModel, )
        fields = ('name', 'playlists')
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'
