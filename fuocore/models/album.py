from enum import Enum

from .base import ModelType, BaseModel, _get_artists_name


class AlbumType(Enum):
    """Album type enumeration

    中文解释::

        Single 和 EP 会有一些交集，在展示时，会在一起展示，比如 Singles & EPs。
        Compilation 和 Retrospective 也会有交集，展示时，也通常放在一起，统称“合辑”。

    References:

    1. https://www.zhihu.com/question/22888388/answer/33255107
    2. https://zh.wikipedia.org/wiki/%E5%90%88%E8%BC%AF
    """
    standard = 'standard'

    single = 'single'
    ep = 'EP'

    live = 'live'

    compilation = 'compilation'
    retrospective = 'retrospective'

    @classmethod
    def guess_by_name(cls, name):
        """guess album type by its name"""

        # album name which contains following string are `Single`
        #   1. ' - Single'  6+3=9
        #   2. '(single)'   6+2=8
        #   3. '（single）'  6+2=8
        if 'single' in name[-9:].lower():
            return cls.single

        # ' - EP'
        if 'ep' in name[-5:].lower():
            return cls.ep

        if 'live' in name or '演唱会' in name or \
           '音乐会' in name:
            return cls.live

        # '精选集', '精选'
        if '精选' in name[-3:]:
            return cls.retrospective

        return cls.standard


class AlbumModel(BaseModel):
    class Meta:
        model_type = ModelType.album.value

        # TODO: 之后可能需要给 Album 多加一个字段用来分开表示 artist 和 singer
        # 从意思上来区分的话：artist 是专辑制作人，singer 是演唱者
        # 像虾米音乐中，它即提供了专辑制作人信息，也提供了 singer 信息
        fields = ['name', 'cover', 'songs', 'artists', 'desc', 'type']
        fields_display = ['name', 'artists_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if kwargs.get('type') is None:
            name = kwargs.get('name')
            if name:
                self.type = AlbumType.guess_by_name(name)
            else:
                self.type = AlbumType.standard

    def __str__(self):
        return 'fuo://{}/albums/{}'.format(self.source, self.identifier)

    @property
    def artists_name(self):
        return _get_artists_name(self.artists or [])
