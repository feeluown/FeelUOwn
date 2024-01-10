from feeluown.library import AbstractProvider
from feeluown.library import (
    ModelFlags,

    BaseModel,
    SongModel,
    ArtistModel,
    AlbumModel,
    PlaylistModel,
    UserModel,
    BriefSongModel,
    BriefArtistModel,
    BriefAlbumModel,
    BriefPlaylistModel,
    BriefUserModel,
)
from feeluown.library import reverse


class ModelSerializerMixin:

    def _get_items(self, model):
        # initialize fields that need to be serialized
        # if as_line option is set, we always use fields_display
        if self.opt_as_line or self.opt_brief:
            if ModelFlags.v2 in model.meta.flags:
                modelcls = type(model)
                fields = [field for field in model.__fields__
                          if field not in BaseModel.__fields__]
                # Include properties.
                pydantic_fields = ("__values__", "fields", "__fields_set__",
                                   "model_computed_fields", "model_extra",
                                   "model_fields_set")
                fields += [prop for prop in dir(modelcls)
                           if isinstance(getattr(modelcls, prop), property)
                           and prop not in pydantic_fields]
            else:
                fields = model.meta.fields_display
        else:
            fields = self._declared_fields
        items = [("provider", model.source),
                 ("identifier", str(model.identifier)),
                 ("uri", reverse(model))]
        if self.opt_fetch:
            for field in fields:
                items.append((field, getattr(model, field)))
        else:
            for field in fields:
                items.append((field, getattr(model, field + '_display')))
        return items


class SongSerializerMixin:
    class Meta:
        types = (SongModel, BriefSongModel)
        # since url can be too long, we put it at last
        fields = ('title', 'duration', 'album', 'artists')
        line_fmt = '{uri:{uri_length}}\t# {title:_18} - {artists_name:_20}'


class ArtistSerializerMixin:
    class Meta:
        types = (ArtistModel, BriefArtistModel)
        fields = ('name', 'songs')
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'


class AlbumSerializerMixin:
    class Meta:
        types = (AlbumModel, BriefAlbumModel)
        fields = ('name', 'artists', 'songs')
        line_fmt = '{uri:{uri_length}}\t# {name:_18} - {artists_name:_20}'


class PlaylistSerializerMixin:
    class Meta:
        types = (PlaylistModel, BriefPlaylistModel)
        fields = ('name', )
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'


class UserSerializerMixin:
    class Meta:
        types = (UserModel, BriefUserModel)
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
        types = ()

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
