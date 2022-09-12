from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, AtomDataType
from mutagen.flac import FLAC


def read_audio_cover(fpath):
    """read audio cover binary data and format"""

    if fpath.endswith('mp3'):
        mp3 = MP3(fpath)
        apic = mp3.get('APIC:')
        if apic is not None:
            if apic.mime in ('image/jpg', 'image/jpeg'):
                fmt = 'jpg'
            else:
                fmt = 'png'
            return apic.data, fmt

    elif fpath.endswith('m4a'):
        mp4 = MP4(fpath)
        tags = mp4.tags
        if tags is not None:
            covers = tags.get('covr')
            if covers:
                cover = covers[0]
                if cover.imageformat == AtomDataType.JPEG:
                    fmt = 'jpg'
                else:
                    fmt = 'png'
                return cover, fmt

    elif fpath.endswith('flac'):
        flac = FLAC(fpath)
        covers = flac.pictures
        if covers:
            cover = covers[0]
            if cover.mime in ('image/jpg', 'image/jpeg'):
                fmt = 'jpg'
            else:
                fmt = 'png'
            return cover.data, fmt

    return None, None
