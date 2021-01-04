from feeluown.library import AbstractProvider
from feeluown.models import SongModel, ArtistModel, \
    AlbumModel, PlaylistModel, UserModel, SearchModel

from .base import try_cast_model_to_v1


class ModelSerializerMixin:

    def _get_items(self, model):
        model = try_cast_model_to_v1(model)
        # initialize fields that need to be serialized
        # if as_line option is set, we always use fields_display
        if self.opt_as_line or self.opt_brief:
            fields = model.meta.fields_display
        else:
            fields = self._declared_fields
        items = [("provider", model.source),
                 ("identifier", model.identifier),
                 ("uri", str(model))]
        if self.opt_fetch:
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


class SearchSerializerMixin:
    """

    .. note::

        SearchModel isn't a standard model, it does not have identifier,
        the uri of SearchModel instance is also not so graceful, so we handle
        it as a normal object temporarily.
    """

    class Meta:
        types = (SearchModel, )

    def _get_items(self, result):
        fields = ('songs', 'albums', 'artists', 'playlists',)
        items = []
        for field in fields:
            value = getattr(result, field)
            if value:  # only append if it is not empty
                items.append((field, value))
        return items


class ProviderSerializerMixin:
    class Meta:
        types = (AbstractProvider, )

    def _get_items(self, provider):
        """
        :type provider: AbstractProvider
        """
        return [
            ('identifier', provider.identifier),
            ('uri', 'fuo://{}'.format(provider.identifier)),
            ('name', provider.name),
        ]
