from . import BaseModel, ModelType


class VideoModel(BaseModel):

    class Meta:
        model_type = ModelType.video.value
        fields = ['title', 'cover', 'media']
        fields_display = ['title']

    def __str__(self):
        return f'fuo://{self.source}/videos/{self.identifier}'
