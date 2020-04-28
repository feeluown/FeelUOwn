from fuocore.media import MultiQualityMixin, Quality
from .base import BaseModel


class MvModel(BaseModel, MultiQualityMixin):
    QualityCls = Quality.Video

    class Meta:
        fields = ['name', 'media', 'desc', 'cover', 'artist']
        support_multi_quality = False
