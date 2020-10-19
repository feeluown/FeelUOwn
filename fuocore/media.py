import re
from enum import Enum


class Quality:
    """

    >>> [Quality.Audio.best(), Quality.Audio.worst()]
    [<Audio.shq: 'shq'>, <Audio.lq: 'lq'>]
    >>> Quality.SortPolicy.apply('hq><', ['shq', 'hq', 'sq', 'lq'])
    ['hq', 'sq', 'shq', 'lq']
    >>> Quality.SortPolicy.apply('>>>', [3, 2, 1])
    [3, 2, 1]
    """

    class SortPolicy:
        """media sort policy

        For example, when the quality list is: ``[hp, h, s, l]``,
        then policy will be interpreted like this::

            h<<> = h -> hp -> s  -> l
            h>>> = h -> s  -> l  -> hp
            h><  = h -> s  -> hp -> l
            h<>  = h -> hp -> s  -> l
            >>>  = hp -> h -> s  -> l  # doctest: +SKIP
            <<<  = l -> s -> h -> hp

        Code Example::

            policy = 'hq<>'  # priority: hq shq sq lq
            song.select_media(policy)
            song.select_media('>>>')  # shq hq sq lq

            video_policy = 'sd<>'  # priority: sd hd ld fhd
            video.select_media(video_policy)
        """

        #: policy rules, {name:regex} mapping
        rules = (
            ('rlrl', r'(\w+)><'),
            ('lrlr', r'(\w+)<>'),
            ('llr', r'(\w+)<<>'),
            ('rrl', r'(\w+)>><'),
            ('rrr', r'(\w+)?>>>'),
            ('lll', r'(\w+)?<<<'),
        )

        @classmethod
        def apply(cls, source, l):  # noqa: E741
            """sort the list L using the policy parsed from SOURCE

            :param source: policy source string
            :param l: quality value list
            :return: sorted quality value list
            :raise ValueError: policy source string is invalid
            """
            rule, q = cls._parse(source)
            if rule in ('rrr', 'lll'):
                return l if rule == 'rrr' else l[::-1]
            q_idx = cls._get_index(q, l)
            new_l = [q]
            left = l[:q_idx][::-1]
            right = l[q_idx+1:]
            if rule == 'rrl':
                new_l = right + new_l + left
            elif rule == 'llr':
                new_l = left + new_l + right
            elif rule == 'rlrl':
                new_l += cls._cross_merge_list(right, left)
            else:  # rule == 'lrlr'
                new_l += cls._cross_merge_list(left, right)
            return new_l

        @classmethod
        def _parse(cls, source):
            """extract a policy oject from the policy string

            temporarily, the policy object is a tuple, e.g., ('rlrl', 'hq').
            """
            for name, p in cls.rules:
                regex = re.compile(p)
                m = regex.match(source)
                if m is not None:
                    return name, m.group(1)
            raise ValueError('invalid policy string: rule not found')

        @staticmethod
        def _cross_merge_list(l1, l2):
            """
            >>> Quality.SortPolicy._cross_merge_list([1, 2], [3])
            [1, 3, 2]
            >>> Quality.SortPolicy._cross_merge_list([3], [1, 2])
            [3, 1, 2]
            """
            i = 0
            l = []  # noqa: E741
            while i < len(l1) and i < len(l2):
                l.append(l1[i])
                l.append(l2[i])
                i += 1
            if i < len(l1):
                l += l1[i:]  # noqa: E741
            if i < len(l2):
                l += l2[i:]  # noqa: E741
            return l

        @staticmethod
        def _get_index(q, l):  # noqa: E741
            try:
                q_idx = l.index(q)
            except ValueError:
                raise ValueError('invalid policy string: quality not found')
            return q_idx

    class Mixin:
        @classmethod
        def best(cls):
            return list(cls)[0]

        @classmethod
        def worst(cls):
            return list(cls)[-1]

    class Audio(Mixin, Enum):
        shq = 'shq'  #: super high quality(>320kbps)
        hq = 'hq'    #: high quality(~=320kbps)
        sq = 'sq'    #: standard quality(~=200kbps)
        lq = 'lq'    #: low quality(~=100kbps)

    class Video(Mixin, Enum):
        fhd = 'fhd'  #: full high definition
        hd = 'hd'    #: high definition
        sd = 'sd'    #: standard definition
        ld = 'ld'    #: low definition


class MultiQualityMixin:
    def list_quality(self):
        """list available quality"""

    def select_media(self, policy=None):
        """select a media by quality(and fallback policy)

        :param policy: fallback priority/policy
        """
        # fetch available quality list
        available_q_set = set(self.list_quality())
        if not available_q_set:
            return None, None

        QualityCls = self.QualityCls
        # translate policy into quality priority list
        if policy is None:
            if QualityCls == Quality.Audio:
                policy = 'hq<>'
            else:  # Quality.Video
                policy = 'hd<>'
        sorted_q_list = Quality.SortPolicy.apply(
            policy, [each.value for each in list(QualityCls)])

        # find the first available quality
        for quality in sorted_q_list:
            if quality in available_q_set:
                break
        return self.get_media(quality), quality

    def get_media(self, quality):
        """get media by quality

        if q is not available, return None.
        """


class MediaType:
    audio = 'audio'
    video = 'video'
    image = 'image'


class AudioMeta:
    def __init__(self, bitrate=None, format=None):
        #: audio bitrate, unit is kbps, int
        self.bitrate = bitrate
        #: audio format, string
        self.format = format

    def __repr__(self):
        return '<AudioMeta format={format} bitrate={bitrate}>'.format(
            format=self.format,
            bitrate=self.bitrate,
        )


class ImageMeta:
    def __init__(self, size=None, format=None):
        self.size = size
        self.format = format


TYPE_METACLS_MAP = {
    MediaType.audio: AudioMeta,
    MediaType.image: ImageMeta,
}


class Media:

    def __init__(self, url, type_=MediaType.audio, http_headers=None,
                 **kwargs):
        if isinstance(url, Media):
            self._copy(url)
            return
        self.url = url
        self.type_ = type_

        metacls = TYPE_METACLS_MAP[type_]
        self._metadata = metacls(**kwargs)

        # network options
        self.http_headers = http_headers or {}

    def _copy(self, media):
        self.url = media.url
        self.http_headers = media.http_headers
        self.type_ = media.type_
        self._metadata = media._metadata

    @property
    def metadata(self):
        return self._metadata
