from fuocore.models import BaseModel, SongModel, ArtistModel, \
    AlbumModel, PlaylistModel, UserModel


def serialize_model(model, root_serializer):
    #
    # setup root_serializer
    #
    root_serializer.setup()

    # initialize fields that need to be serialized
    # if as_line option is set, we always use fields_display
    if root_serializer.options['as_line'] or root_serializer.options['brief']:
        fields = model.meta.fields_display
    else:
        fields = root_serializer._declared_fields

    # keep the fields order
    common_fields = ['provider', 'identifier', 'uri']
    all_fields = common_fields + list(fields)

    #
    # before handle each field
    #
    root_serializer.before_handle_field(model, all_fields)

    #
    # handle each field
    #
    store = {"provider": model.source,
             "identifier": model.identifier,
             "uri": str(model)}
    for field in fields:
        obj = getattr(
            model,
            field if root_serializer.options['fetch'] else field + "_display"
        )
        store[field] = obj
    for field, value in store.items():
        serializer_cls = root_serializer.get_serializer_cls(value)
        serializer = serializer_cls(brief=True,
                                    fetch=False,
                                    as_line=True)
        value = serializer.serialize(value)
        root_serializer.handle_field(field, value)

    #
    # after handle each field
    #
    root_serializer.after_handle_field(model, all_fields)

    # TODO: use streaming if root_serializer support
    # Theoretically, yaml and plain root_serializer support streaming
    result = root_serializer.get_result()

    #
    # do some cleanup
    #
    root_serializer.teardown()
    return result


class SongSerializerMixin:
    class Meta:
        types = (SongModel, )
        fields = ('title', 'duration', 'url', 'artists', 'album')
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
