import random

from feeluown.collection import Collection
from feeluown.library import BriefSongModel, ModelType, reverse, BriefAlbumModel, BriefArtistModel


def song2line(song: BriefSongModel):
    line = reverse(song, as_line=True)
    parts = line.split('#', 1)
    if len(parts) >= 2:
        return parts[1]
    return None


def artist2line(artist: BriefArtistModel):
    line = reverse(artist, as_line=True)
    parts = line.split('#', 1)
    if len(parts) >= 2:
        return parts[1]
    return None


def album2line(album: BriefAlbumModel):
    line = reverse(album, as_line=True)
    parts = line.split('#', 1)
    if len(parts) >= 2:
        return parts[1]
    return None


async def generate_prompt_for_library(library: Collection):
    """Generate prompt based on the user's music library.
    """
    songs = []
    artists = []
    albums = []
    for model in library.models:
        if ModelType(model.meta.model_type) is ModelType.song:
            songs.append(model)
        elif ModelType(model.meta.model_type) is ModelType.artist:
            artists.append(model)
        elif ModelType(model.meta.model_type) is ModelType.album:
            albums.append(model)
    random.shuffle(songs)
    random.shuffle(artists)
    random.shuffle(albums)
    random_songs = songs[:10]
    random_artists = artists[:10]
    random_albums = albums[:10]

    song_lines = []
    for song in random_songs:
        line = song2line(song)
        if line:
            song_lines.append('    ' + line)
    songs_text = '\n'.join(song_lines)

    artist_lines = []
    for artist in random_artists:
        line = artist2line(artist)
        if line:
            artist_lines.append('    ' + line)
    artists_text = '\n'.join(artist_lines)

    album_lines = []
    for album in random_albums:
        line = album2line(album)
        if line:
            album_lines.append('    ' + line)
    albums_text = '\n'.join(album_lines)

    prompt_text = f"""用户的音乐库包含以下内容：
歌曲（总数：{len(songs)}，随机抽取 {len(song_lines)} 首）：
{songs_text}
歌手（总数：{len(artists)}，随机抽取 {len(artist_lines)} 名）：
{artists_text}
专辑（总数：{len(albums)}，随机抽取 {len(album_lines)} 个）：
{albums_text}
"""
    return prompt_text

