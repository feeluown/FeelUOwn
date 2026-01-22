### Locallication for FeelUOwn

# Common translation
# This is for common buttons, like:
# minimize, fullscreen, close, e.g.
# ----------------------------------------
minimize-window = Minimize
fullscreen-window = Full Screen
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

# feeluown.version
# ----------------------------------------
new-version-found = Found new version { $latestVer }, current: { $currentVer }
already-updated = Already updated: { $latestVer }

# feeluown.local
# ----------------------------------------
local-tracks-scan-finished = Local tracks scan finished!
# feeluown.local.provider
# ----------------------------------------
local-tracks = Local tracks

# feeluown.gui.tips
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

# feeluown.gui.watch
# ----------------------------------------
picture-in-picture = Picture-in-Picture
hide-picture-in-picture = Exit { picture-in-picture } mode

# feeluown.gui.components
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.components.avatar
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

# feeluown.gui.components.btns
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

# feeluown.gui.components.collections
# ----------------------------------------
track-collection = Collection
remove-this-collection = Remove this { track-collection }

# feeluown.gui.components.line_song
# ----------------------------------------
play-stage-prepare-track-url = Obtaining {track} playback URL...
play-stage-prepare-track-url-fallback = Attempting to find a fallback playback URL...
play-stage-prepare-track-metadata = Attempting to fetch complete track metadata...
play-stage-prepare-track-loading = Loading {track} resources...
play-stage-prepare-movie-url = Obtaining {video} playback URL for the music...

# feeluown.gui.components.menu
# ----------------------------------------
play-track-movie = Play MV
track-missing-album = No { album } information for this { track }
track-missing-movie = { track } has no MV
track-search-similar = Search for similar resources
track-show-artist = View { musician }
track-show-album = View { album }
track-enter-radio = { track } Radio
track-show-detail = { track } Details

track-playlist-add = Add to { playlist }
track-playlist-add-succ = Added to { $playlistName } ✅
track-playlist-add-fail = Failed to add to { $playlistName } ❌

track-movie-missing = No MV for this { track }

menu-ai-prompt =
    You are a music player assistant.
    \[your request here\]
    The song information is as follows -> Song Title: { $songTitle }, Artist: { $songArtists }
menu-ai-button = AI
menu-ai-copy-prompt = Copy AI Prompt
menu-ai-copy-prompt-succeed = Copied to clipboard

# feeluown.gui.components.nowplaying
# ----------------------------------------
track-movie-play-tooltip = Play { track } MV
track-album-release-date = Album Release Date: { $releaseDate }

# feeluown.gui.components.player_playlist
# ----------------------------------------
fm-radio-current-song-dislike = Dislike
track-playlist-remove = Remove from { playlist }

track-provider-blacklist-add = Add to provider's blacklist
track-provider-blacklist-adding = Adding to blacklist, please wait...
track-provider-blacklist-add-succ = Added to provider's blacklist
track-provider-blacklist-add-fail = Failed to add to blacklist

track-radio-mode-remove-latest = In FM mode, if the current song is the last one, it cannot be removed. Please try again later.

# feeluown.gui.components.playlist_btn
# ----------------------------------------
playlist-show = Show current { playlist }

# feeluown.gui.components.search
# ----------------------------------------

track-search = Search { $keyword }

## providerCount: count of content providers.
track-searching = Searching { $providerCount } content providers...

## providerName: name of the content provider
track-search-error = Error searching from { $providerName }: { $errorMessage }
track-search-result-empty = Searching { $providerName } yielded no results

## resultCount: amount of valid results
## timeCost: seconds cost for searching, floating number
track-search-done = Search completed, with { $resultCount } valid results, taking {
   NUMBER($timeCost, minimumFractionDigits: 2, maximumFractionDigits: 2)
}s

# feeluown.gui.widgets
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.widgets.labels
# ----------------------------------------
error-message-prefix = Error:{" "}
info-message-prefix = Note:{" "}

# feeluown.gui.widgets.selfpaint_btn
# ----------------------------------------
discovery = Discovery
homepage = Home
calender = Calender
top-list = Top list
favorites = Favorites
hot = Hot
emoji-expression = Emoji

# feeluown.gui.widgets.magicbox
# ----------------------------------------
search-box-placeholder = Search songs, artists, albums, users
search-box-tooltip =
    Type text directly to filter, press Enter to search
    Input >>> prefix to execute Python code
    Input "==> Playing Without Regret | Faye Wong" to play a song directly
    Input "=== What to listen on a rainy day?" to interact with AI
    Input # prefix to filter table content
    Input > prefix to execute fuo command (not implemented, PR welcome)
search-box-ai-chat-unavailable = AI chat is unavailable
search-box-play-track = Attempt to play: { $song }
search-box-play-track-ill-formed = Your input must follow the format: "Song Title | Artist Name"

# feeluown.gui.widgets.settings
# ----------------------------------------
app-config = App Configuration
save-config = Save
search-providers = Search Providers
ai-radio-prompt = AI Radio (Prompt)
player = Player

# feeluown.gui.widgets.login
# ----------------------------------------
cookies-dialog-login-button  = Login
cookies-dialog-web-login-btn = Use FeelUOwn built-in browser to login
cookies-dialog-chrome-btn    = Read cookies from Chrome
cookies-dialog-firefox-btn   = Read cookies from Firefox
cookies-dialog-edge-btn      = Read cookies from Edge

cookies-dialog-tutorial =
    FeelUOwn offers several ways to log in to third-party music platforms,
    <span style='color:red'>choose whichever you like</span>.<br/><br/>
    If you are already logged into a third-party platform in your usual browser, you can prioritize the “Read Cookie” login method.
    Otherwise, it is recommended to use the "{ cookies-dialog-web-login-btn }" method (you need to install pyqt webengine to use it).
    Of course, if you know how to manually copy cookies, you can copy them first and then click “Login”.

cookies-dialog-placeholder =
    Please copy cookies from the browser!

    You can copy a request’s Cookie header in the format key1=value1; key2=value2
    Or you can enter cookie content in JSON format, like {"{"}"key1": "value1", "key2": "value2"{"}"}

cookies-parse-fail    = Failed to parse with { $parser }, trying next
cookies-parse-success = Successfully parsed with { $parser }

cookies-save-user-info        = Saving user info to FeelUOwn data directory
cookies-loading-existing-user = Attempting to load existing user...

# feeluown.gui.widgets.songs
# ----------------------------------------
add-to-playlist = Add to playlist
remove-from-playlist = Remove song

# feeluown.gui.uimain
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.uimain.playlist_overlay
# ----------------------------------------
playlist-clear = Clear { playlist }
jump-to-playing-track = Current track

song-radio-mode = Song radio mode
song-radio-mode-empty-playlist = Playback queue is empty, cannot activate the { song-radio-mode }
song-radio-mode-activated = '{ song-radio-mode }' activated

playback-mode = Playback Mode
playback-mode-change = Change { playback-mode }
playback-mode-single-repeat = Single Repeat
## play songs in original order, on end stop playing
playback-mode-sequential = Sequential
## play songs in original order, on end back to the first
playback-mode-loop = Loop
## play songs in random order
playback-mode-random = Random

# feeluown.gui.uimain.nowplaying_overlay
# ----------------------------------------
similar-tracks = Similar{track}
track-hot-comments = Hot comments
movie-mode-exit = Exit movie mode

# feeluown.gui.pages.song_explore
# ----------------------------------------
track-lyrics = Lyrics
track-start-play = Play
track-webpage-url-copy = Copy webpage URL
track-belongs-album = Belongs to album
release-date = Release date
track-genre = Genre

error-message-template =
    <p style=color: grey; font: small;>This provider does not yet support{"{"}feature{"}"}.
    <br/> Implement the { $interface } interface to support this feature ~
    </p>
find-similar-tracks = View{ similar-tracks }
track-view-comments = View{ track } comments

# feelown.gui.pages
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.pages.homepage
# ----------------------------------------
fold-expand = Expand
fold-collapse = Collapse
fold-tooltip = {fold-expand}/{fold-collapse}

recommended-playlist = Recommended {track-list}s
recommended-daily-playlist = Daily Recommendations
recommended-feelin-lucky = Just listening
recommended-videos = Take a look
recommended-videos-missing = No recommended {video}

# feeluown.gui.pages.my_fav.py
# ----------------------------------------

## providerName: [string] name of the provider
## mediaType: [string] can be one of:
##    track
##    album
##    singer
##    playlist
##    video
provider-missing-favorite = Provider { $providerName } doesn't support Liked { $mediaType ->
    [track] {track}
    [album] {album}
    [singer] {musician}
    [playlist] {track-list}
    [video] {video}
   *[other] Contents
}
provider-unknown-cannot-view = Provider unknown, cannot view this page
my-favorite-title = My favorites
