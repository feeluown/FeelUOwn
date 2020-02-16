from fuocore.models import SongModel, ArtistModel, \
    AlbumModel, PlaylistModel, UserModel


simple_fields = set({'title', 'duration', 'url',
                     'name', 'artists_name', 'album_name'})


class ModelSerializerMixin:
    def serialize(self, model):
        # initialize fields that need to be serialized
        # if as_line option is set, we always use fields_display
        if self.options['as_line'] or self.options['brief']:
            fields = model.meta.fields_display
            are_display_fields = True
        else:
            fields = self._declared_fields
            are_display_fields = False

        # keep the fields order
        common_fields = ['provider', 'identifier', 'uri']
        all_fields = common_fields + list(fields)

        #
        # setup self
        #
        self.setup(model, all_fields)

        #
        # handle each field
        #
        # perf: since we know these fields will not change after serialization,
        # so we handle them directly
        self.handle_field("provider", model.source)
        self.handle_field("identifier", model.identifier)
        self.handle_field("uri", str(model))
        for field in fields:
            if are_display_fields is True:
                value = getattr(model, field + "_display")
                # perf: display field's value is a string, handle them directly
                self.handle_field(field, value)
            else:
                value = getattr(model, field)
                serializer_cls = self.get_serializer_cls(value)
                serializer = serializer_cls(brief=True, fetch=False, as_line=True)
                value = serializer.serialize(value)
                self.handle_field(field, value)

        # TODO: use streaming if self support
        # Theoretically, yaml and plain self support streaming
        result = self.get_result()

        #
        # do some cleanup
        #
        self.teardown()
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
