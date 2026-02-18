from typing import Any

from mcp.server.fastmcp import FastMCP
from feeluown.app import App, get_app
from feeluown.library import (
    ResolveFailed,
    ResolverNotFound,
    resolve,
    reverse,
    SearchType,
    BriefSongModel,
    BriefVideoModel,
)
from feeluown.library.provider_protocol import (
    SupportsAlbumGet,
    SupportsArtistGet,
    SupportsCurrentUser,
    SupportsCurrentUserListPlaylists,
    SupportsCurrentUserListRadioSongs,
    SupportsRecACollectionOfSongs,
    SupportsRecACollectionOfVideos,
    SupportsRecListCollections,
    SupportsRecListDailyAlbums,
    SupportsRecListDailyPlaylists,
    SupportsRecListDailySongs,
    SupportsPlaylistGet,
    SupportsSongSimilar,
    SupportsToplist,
    SupportsPlaylistCreateByName,
    SupportsPlaylistDelete,
    SupportsPlaylistAddSong,
    SupportsPlaylistRemoveSong,
    SupportsSongGet,
    SupportsSongMV,
    SupportsSongLyric,
    SupportsSongWebUrl,
    SupportsVideoGet,
    SupportsVideoWebUrl,
)
from feeluown.serializers import serialize


mcp = FastMCP("FeelUOwn")
_PROTOCOLS = (
    SupportsAlbumGet,
    SupportsArtistGet,
    SupportsCurrentUser,
    SupportsCurrentUserListPlaylists,
    SupportsCurrentUserListRadioSongs,
    SupportsRecACollectionOfSongs,
    SupportsRecACollectionOfVideos,
    SupportsRecListCollections,
    SupportsRecListDailyAlbums,
    SupportsRecListDailyPlaylists,
    SupportsRecListDailySongs,
    SupportsPlaylistGet,
    SupportsSongSimilar,
    SupportsToplist,
    SupportsPlaylistCreateByName,
    SupportsPlaylistDelete,
    SupportsPlaylistAddSong,
    SupportsPlaylistRemoveSong,
    SupportsSongGet,
    SupportsSongMV,
    SupportsSongLyric,
    SupportsSongWebUrl,
    SupportsVideoGet,
    SupportsVideoWebUrl,
)


def _require_app() -> App:
    app = get_app()
    if app is None:
        raise RuntimeError("app is not initialized")
    return app


def _player_nowplaying_metadata() -> dict[str, Any] | None:
    app = _require_app()
    return serialize("python", app.player.current_metadata)


def _playlist_list() -> list[dict[str, Any]]:
    app = _require_app()
    return serialize("python", app.playlist.list())


def _player_play_media_by_uri(uri: str) -> bool:
    app = _require_app()
    for model in app.playlist.list():
        if reverse(model) == uri:
            app.playlist.play_model(model)
            return True
    return False


def _current_song_uri() -> str | None:
    app = _require_app()
    song = app.playlist.current_song
    if song is None:
        return None
    return reverse(song)


def _provider_protocols(provider) -> list[str]:
    return [proto.__name__ for proto in _PROTOCOLS if isinstance(provider, proto)]


def _provider_from_id(provider_id: str):
    app = _require_app()
    return app.library.get(provider_id)


def _limit_search_payload(payload: dict[str, Any], limit: int | None) -> dict[str, Any]:
    if limit is None:
        return payload
    limited: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, list):
            limited[key] = value[: max(limit, 0)]
        else:
            limited[key] = value
    return limited


def _limit_models(models: list[Any], limit: int | None) -> list[Any]:
    if limit is None:
        return list(models)
    return list(models)[: max(limit, 0)]


def _serialize_collection(collection) -> dict[str, Any]:
    return {
        "name": collection.name,
        "type": collection.type_.name,
        "description": collection.description,
        "models": serialize("python", collection.models),
    }


def _provider_model_get(
    provider_id: str, identifier: str, protocol, getter_name: str
) -> dict[str, Any] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, protocol):
        return None
    try:
        model = getattr(provider, getter_name)(identifier)
    except Exception:
        return None
    if model is None:
        return None
    return serialize("python", model)


def _build_brief_song(provider_id: str, song_id: str) -> BriefSongModel:
    return BriefSongModel(identifier=song_id, source=provider_id)


def _build_brief_video(provider_id: str, video_id: str) -> BriefVideoModel:
    return BriefVideoModel(identifier=video_id, source=provider_id)


@mcp.tool()
def player_nowplaying_metadata() -> dict[str, Any] | None:
    """
    Get the metadata of the currently playing track.
    """
    return _player_nowplaying_metadata()


@mcp.resource("fuo://player/playlist")
def playlist_list() -> list[dict[str, Any]]:
    """
    List all tracks in the current playlist queue.
    Each item includes a `uri` field.
    """
    return _playlist_list()


@mcp.resource("fuo://player/nowplaying")
def nowplaying() -> dict[str, Any] | None:
    """
    Get the current playing track info.
    """
    metadata = _player_nowplaying_metadata()
    if metadata is None:
        return None
    return {
        "uri": _current_song_uri(),
        "metadata": metadata,
    }


@mcp.resource("fuo://library/providers")
def library_providers() -> list[dict[str, Any]]:
    app = _require_app()
    providers = []
    for provider in app.library.list():
        providers.append(
            {
                "id": provider.identifier,
                "name": provider.name,
            }
        )
    return providers


@mcp.tool()
def player_play_media_by_uri(uri: str) -> bool:
    """
    Play a track by URI if it exists in the current playlist queue.
    """
    return _player_play_media_by_uri(uri)


@mcp.tool()
def player_toggle() -> None:
    _require_app().player.toggle()


@mcp.tool()
def player_play() -> None:
    _require_app().player.resume()


@mcp.tool()
def player_pause() -> None:
    _require_app().player.pause()


@mcp.tool()
def player_seek(position: float) -> None:
    _require_app().player.position = position


@mcp.tool()
def player_status() -> dict[str, Any]:
    app = _require_app()
    player = app.player
    playlist = app.playlist
    return {
        "state": player.state.name,
        "position": player.position,
        "duration": player.duration,
        "volume": player.volume,
        "playback_mode": playlist.playback_mode.name,
        "nowplaying": nowplaying(),
    }


@mcp.tool()
def playlist_next() -> None:
    _require_app().playlist.next()


@mcp.tool()
def playlist_previous() -> None:
    _require_app().playlist.previous()


@mcp.tool()
def playlist_clear() -> None:
    _require_app().playlist.clear()


@mcp.tool()
def playlist_add_uri(uri: str) -> bool:
    app = _require_app()
    try:
        model = resolve(uri)
    except (ResolveFailed, ResolverNotFound):
        return False
    app.playlist.add(model)
    return True


@mcp.tool()
def playlist_play_uri(uri: str) -> bool:
    app = _require_app()
    try:
        model = resolve(uri)
    except (ResolveFailed, ResolverNotFound):
        return False
    app.playlist.add(model)
    app.playlist.play_model(model)
    return True


@mcp.tool()
def provider_capabilities(provider_id: str) -> dict[str, Any] | None:
    app = _require_app()
    provider = app.library.get(provider_id)
    if provider is None:
        return None
    return {
        "id": provider.identifier,
        "name": provider.name,
        "protocols": _provider_protocols(provider),
    }


@mcp.tool()
def provider_search(
    provider_id: str,
    keyword: str,
    type_in: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]] | None:
    """
    Search provider resources. Returns a list of results per search type.
    """
    provider = _provider_from_id(provider_id)
    if provider is None:
        return None
    try:
        types = SearchType.batch_parse(type_in) if type_in else [SearchType.so]
    except ValueError:
        return None
    results = []
    for type_ in types:
        try:
            result = provider.search(keyword=keyword, type_=type_)
        except Exception:
            continue
        if result is None:
            continue
        payload = serialize("python", result)
        payload = _limit_search_payload(payload, limit)
        results.append(
            {
                "type": type_.value,
                "source": provider.identifier,
                "result": payload,
            }
        )
    return results


@mcp.tool()
def provider_rec_list_daily_songs(
    provider_id: str, limit: int | None = None
) -> list[dict[str, Any]] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsRecListDailySongs):
        return None
    try:
        songs = provider.rec_list_daily_songs()
    except Exception:
        return None
    if songs is None:
        return None
    return serialize("python", _limit_models(songs, limit))


@mcp.tool()
def provider_rec_list_daily_playlists(
    provider_id: str, limit: int | None = None
) -> list[dict[str, Any]] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsRecListDailyPlaylists):
        return None
    try:
        playlists = provider.rec_list_daily_playlists()
    except Exception:
        return None
    if playlists is None:
        return None
    return serialize("python", _limit_models(playlists, limit))


@mcp.tool()
def provider_rec_list_daily_albums(
    provider_id: str, limit: int | None = None
) -> list[dict[str, Any]] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsRecListDailyAlbums):
        return None
    try:
        albums = provider.rec_list_daily_albums()
    except Exception:
        return None
    if albums is None:
        return None
    return serialize("python", _limit_models(albums, limit))


@mcp.tool()
def provider_rec_list_collections(
    provider_id: str, limit: int | None = None
) -> list[dict[str, Any]] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsRecListCollections):
        return None
    try:
        collections = provider.rec_list_collections(limit=limit)
    except Exception:
        return None
    if collections is None:
        return None
    return [_serialize_collection(collection) for collection in collections]


@mcp.tool()
def provider_rec_a_collection_of_songs(provider_id: str) -> dict[str, Any] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsRecACollectionOfSongs):
        return None
    try:
        collection = provider.rec_a_collection_of_songs()
    except Exception:
        return None
    return _serialize_collection(collection)


@mcp.tool()
def provider_rec_a_collection_of_videos(provider_id: str) -> dict[str, Any] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsRecACollectionOfVideos):
        return None
    try:
        collection = provider.rec_a_collection_of_videos()
    except Exception:
        return None
    return _serialize_collection(collection)


@mcp.tool()
def provider_toplist_list(
    provider_id: str, limit: int | None = None
) -> list[dict[str, Any]] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsToplist):
        return None
    try:
        toplists = provider.toplist_list()
    except Exception:
        return None
    if toplists is None:
        return None
    return serialize("python", _limit_models(toplists, limit))


@mcp.tool()
def provider_toplist_get(provider_id: str, toplist_id: str) -> dict[str, Any] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsToplist):
        return None
    try:
        playlist = provider.toplist_get(toplist_id)
    except Exception:
        return None
    if playlist is None:
        return None
    return serialize("python", playlist)


@mcp.tool()
def provider_song_get_lyric(provider_id: str, song_id: str) -> dict[str, Any] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsSongLyric):
        return None
    try:
        lyric = provider.song_get_lyric(_build_brief_song(provider_id, song_id))
    except Exception:
        return None
    if lyric is None:
        return None
    return serialize("python", lyric)


@mcp.tool()
def provider_song_get_web_url(provider_id: str, song_id: str) -> str | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsSongWebUrl):
        return None
    try:
        return provider.song_get_web_url(_build_brief_song(provider_id, song_id))
    except Exception:
        return None


@mcp.tool()
def provider_song_get_mv(provider_id: str, song_id: str) -> dict[str, Any] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsSongMV):
        return None
    try:
        video = provider.song_get_mv(_build_brief_song(provider_id, song_id))
    except Exception:
        return None
    if video is None:
        return None
    return serialize("python", video)


@mcp.tool()
def provider_song_list_similar(
    provider_id: str, song_id: str, limit: int | None = None
) -> list[dict[str, Any]] | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsSongSimilar):
        return None
    try:
        songs = provider.song_list_similar(_build_brief_song(provider_id, song_id))
    except Exception:
        return None
    if songs is None:
        return None
    return serialize("python", _limit_models(songs, limit))


@mcp.tool()
def provider_video_get_web_url(provider_id: str, video_id: str) -> str | None:
    provider = _provider_from_id(provider_id)
    if provider is None or not isinstance(provider, SupportsVideoWebUrl):
        return None
    try:
        return provider.video_get_web_url(_build_brief_video(provider_id, video_id))
    except Exception:
        return None


@mcp.tool()
def provider_song_get(provider_id: str, song_id: str) -> dict[str, Any] | None:
    """
    Get a song model by provider and identifier.
    """
    return _provider_model_get(provider_id, song_id, SupportsSongGet, "song_get")


@mcp.tool()
def provider_album_get(provider_id: str, album_id: str) -> dict[str, Any] | None:
    """
    Get an album model by provider and identifier.
    """
    return _provider_model_get(provider_id, album_id, SupportsAlbumGet, "album_get")


@mcp.tool()
def provider_artist_get(provider_id: str, artist_id: str) -> dict[str, Any] | None:
    """
    Get an artist model by provider and identifier.
    """
    return _provider_model_get(provider_id, artist_id, SupportsArtistGet, "artist_get")


@mcp.tool()
def provider_playlist_get(provider_id: str, playlist_id: str) -> dict[str, Any] | None:
    """
    Get a playlist model by provider and identifier.
    """
    return _provider_model_get(
        provider_id, playlist_id, SupportsPlaylistGet, "playlist_get"
    )


@mcp.tool()
def provider_video_get(provider_id: str, video_id: str) -> dict[str, Any] | None:
    """
    Get a video model by provider and identifier.
    """
    return _provider_model_get(provider_id, video_id, SupportsVideoGet, "video_get")


def run_mcp_server(host: str = "127.0.0.1", port: int = 23335, debug: bool = False):
    """
    Run the MCP server in Streamable HTTP mode.
    """
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.settings.debug = debug
    mcp.settings.log_level = "DEBUG" if debug else "WARNING"
    return mcp.run_streamable_http_async()
