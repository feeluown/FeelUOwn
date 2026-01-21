### Locallication for FeelUOwn

# Common translation
# This is for common buttons, like:
# minimize, fullscreen, close, e.g.
# ----------------------------------------
minimize-window = Minimize
fullscreen-window = Fullscreen
playlist = Playlist
recently-played = Recently Played

# Tab name, commonly used
# ----------------------------------------
track = Track
## Note: this is for playlists from online providers
## while {playlist} is for tracks play queue.
track-list = Playlist
album = Album
video = Video

## can be the singer, artist, or musician.
musician = Musician

# Version info (feeluown.version)
# ----------------------------------------
new-version-found = Found new version { $latestVer }, current: { $currentVer }
already-updated = Already updated: { $latestVer }

# Local musics (feeluown.local)
# ----------------------------------------
local-tracks-scan-finished = Local tracks scan finished!
# Local musics (feeluown.local.provider)
# ----------------------------------------
local-tracks = Local tracks

# Tips banner (feeluown.gui.tips)
# ----------------------------------------

tips-osdlyrics = Did you know FeelUOwn can work with osdlyrics?
tips-show-more-tips = Type '>>> app.tips_mgr.show_random()' in the search box to see more Tips
tips-album-original-image = Right-click on the album art to view the original image ~
tips-track-drag-to-playlist = You can drag the song to add it to a playlist!
tips-common-tooltip = Hover or right-click for pleasant surprises ~
tips-watch-mode = Enable watch mode to watch MVs while working or studying—how nice is that?

## shortcut: the shortcut key
tips-search-shortcut = The search shortcut is { $shortcut }

## note: $user is passed with prefix '@'
thanks-contributor = Thanks to { $user } for the contribution :)

# Watch mode (feeluown.gui.watch)
# ----------------------------------------
picture-in-picture = Picture-in-Picture
hide-picture-in-picture = Exit { picture-in-picture } mode

# COMPONENTS
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Avatar component (feeluown.gui.components.avatar)
# ----------------------------------------
login-third-party = Login to a third-party platform
some-platform-already-logged = Logged
switch-third-party-account = Change the account

switch-music-platform = Change the platform

## platforms: providers' name conjucted by a comma
## platformsCount: amount of logged providers
logged-accounts-tooltip = Logged: { $platformsCount ->
    [0] None
    *[other] { $platforms }
}

# Buttons component (feeluown.gui.components.btns)
# ----------------------------------------
lyric-button = 词
watch-mode-tooltip =
    When watch mode is enabled, the player will first try to find a suitable { video } to play for the { track }.
    Best practice: when enabling watch, it’s recommended to also enable the { picture-in-picture } mode of the { video }.

local-liked-tracks = the Local favorites
local-liked-tracks-add = Add to { local-liked-tracks }
local-liked-tracks-remove = Remove from { local-liked-tracks }
local-liked-tracks-added = Already added to { local-liked-tracks }
local-liked-tracks-removed = Already removed from { local-liked-tracks }

show-track-movie = Show the { video } screen

# WIDGETS
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Self paint buttons (feeluown.gui.widgets.selfpaint_btn)
# ----------------------------------------
discovery = Discovery
homepage = Home
calender = Calender
top-list = Top list
favorites = Favorites
hot = Hot
emoji-expression = Emoji

# UIMAIN
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

## feeluown.gui.uimain.playlist_overlay
# ----------------------------------------
playlist-clear = Clear { playlist }
jump-to-playing-track = Current track

song-radio-mode = Automatic Song Continuation
song-radio-mode-empty-playlist = Playback queue is empty, cannot activate “{ song-radio-mode }” feature
song-radio-mode-activated = “{ song-radio-mode }” feature activated

playback-mode = Playback Mode
playback-mode-change = Change { playback-mode }
playback-mode-single-repeat = Single Repeat
## play songs in original order, on end stop playing
playback-mode-sequential = Sequential
## play songs in original order, on end back to the first
playback-mode-loop = Loop
## play songs in random order
playback-mode-random = Random
