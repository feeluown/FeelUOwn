### Locallication for FeelUOwn

# Common translation
# This is for common buttons, like:
# minimize, fullscreen, close, e.g.
# ----------------------------------------
minimize-window = Minimize
fullscreen-window = Full Screen
playlist = Playlist
recently-played = Recently Played
-error = Error
-info = Note
-warn = Warning
error = { -error }
info = { -info }
warn = { -warn }
# Tab name, commonly used
# ----------------------------------------
-track = { $capitalization ->
    [uppercase] Track
   *[lowercase] track
}
track = { -track(capitalization: "uppercase") }

## Note: this is for playlists from online providers
## while {playlist} is for tracks play queue.
track-list = Playlist

-album = { $capitalization ->
    [uppercase] Album
   *[lowercase] album
}
album = { -album(capitalization: "uppercase") }
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
tips-album-original-image = Right-click on the { -album } art to view the original image ~
tips-track-drag-to-playlist = You can drag the { -track } to add it to a playlist!
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

logged-accounts-tooltip =
    Logged: { $platformsCount ->
        [0] None
       *[other] { $platforms }
    }
# feeluown.gui.components.btns
# ----------------------------------------
lyric-button = LRC
watch-mode-tooltip =
    When watch mode is enabled, the player will first try to find a suitable { video } to play for the { -track }.
    Best practice: when enabling watch, it’s recommended to also enable the { picture-in-picture } mode of the { video }.
local-liked-tracks = the Local favorites
local-liked-tracks-add = Add to { local-liked-tracks }
local-liked-tracks-remove = Remove from { local-liked-tracks }
local-liked-tracks-added = Already added to { local-liked-tracks }
local-liked-tracks-removed = Already removed from { local-liked-tracks }
show-track-movie = Show the { video } screen
# feeluown.gui.components.collections
# ----------------------------------------
-track-collection ={ $capitalization ->
    [uppercase] Collection
   *[lowercase] collection
}
track-collection = { -track-collection(capitalization: "uppercase") }
remove-this-collection = Remove this { -track-collection }
# feeluown.gui.components.line_song
# ----------------------------------------
play-stage-prepare-track-url = Obtaining { -track } playback URL...
play-stage-prepare-track-url-fallback = Attempting to find a fallback playback URL...
play-stage-prepare-track-metadata = Attempting to fetch complete { -track } metadata...
play-stage-prepare-track-loading = Loading { -track } resources...
play-stage-prepare-movie-url = Obtaining { video } playback URL for the music...
# feeluown.gui.components.menu
# ----------------------------------------
play-track-movie = Play MV
track-missing-album = No { album } information for this { -track }
track-missing-movie = { -track } has no MV
track-search-similar = Search for similar resources
track-show-artist = View { musician }
track-show-album = View { album }
track-enter-radio = { -track } Radio
track-show-detail = { -track } Details
track-playlist-add = Add to { playlist }
track-playlist-add-succ = Added to { $playlistName } ✅
track-playlist-add-fail = Failed to add to { $playlistName } ❌
track-movie-missing = No MV for this { -track }
menu-ai-prompt =
    You are a music player assistant.
        \[your request here\]
        The { -track } information is as follows -> Song Title: { $songTitle }, Artist: { $songArtists }
menu-ai-button = AI
menu-ai-copy-prompt = Copy AI Prompt
menu-ai-copy-prompt-succeed = Copied to clipboard
# feeluown.gui.components.nowplaying
# ----------------------------------------
track-movie-play-tooltip = Play { -track } MV
track-album-release-date = { -album(capitalization: "uppercase") } {release-date}: { $releaseDate }
# feeluown.gui.components.player_playlist
# ----------------------------------------
fm-radio-current-song-dislike = Dislike
track-playlist-remove = Remove from { playlist }
track-provider-blacklist-add = Add to provider's blacklist
track-provider-blacklist-adding = Adding to blacklist, please wait...
track-provider-blacklist-add-succ = Added to provider's blacklist
track-provider-blacklist-add-fail = Failed to add to blacklist
track-radio-mode-remove-latest = In FM mode, if the current { -track } is the last one, it cannot be removed. Please try again later.
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

track-search-done = Search completed, with { $resultCount } valid results, taking { NUMBER($timeCost, minimumFractionDigits: 2, maximumFractionDigits: 2) }s

# feeluown.gui.widgets
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.widgets.labels
# ----------------------------------------
error-message-prefix = { -error }:{ " " }
info-message-prefix = { -info }:{ " " }
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
search-box-placeholder = Search { -track }s, artists, { -alubm }s, users
search-box-tooltip =
    Type text directly to filter, press Enter to search
        Input >>> prefix to execute Python code
        Input "==> Playing Without Regret | Faye Wong" to play a { -track } directly
        Input "=== What to listen on a rainy day?" to interact with AI
        Input # prefix to filter table content
        Input > prefix to execute fuo command (not implemented, PR welcome)
search-box-ai-chat-unavailable = AI chat is unavailable
search-box-play-track = Attempt to play: { $song }
search-box-play-track-ill-formed = Your input must follow the format: "{ -track } title | Artist name"
# feeluown.gui.widgets.settings
# ----------------------------------------
app-config = App Configuration
save-config = Save
search-providers = Search Providers
ai-radio-prompt = AI Radio (Prompt)
player = Player
# feeluown.gui.widgets.login
# ----------------------------------------
cookies-dialog-login-button = Login
cookies-dialog-web-login-btn = Use FeelUOwn built-in browser to login
cookies-dialog-chrome-btn = Read cookies from Chrome
cookies-dialog-firefox-btn = Read cookies from Firefox
cookies-dialog-edge-btn = Read cookies from Edge
cookies-dialog-tutorial =
    FeelUOwn offers several ways to log in to third-party music platforms,
    <span style='color:red'>choose whichever you like</span>.<br/><br/>
    If you are already logged into a third-party platform in your usual browser, you can prioritize the “Read Cookie” login method.
    Otherwise, it is recommended to use the "{ cookies-dialog-web-login-btn }" method (you need to install pyqt webengine to use it).
    Of course, if you know how to manually copy cookies, you can copy them first and then click “Login”.
cookies-dialog-placeholder =
    Please copy cookies from the browser!

    You can copy a request’s Cookie header in the format key1=value1; key2=value2
    Or you can enter cookie content in JSON format, like { "{" }"key1": "value1", "key2": "value2"{ "}" }
cookies-parse-fail = Failed to parse with { $parser }, trying next
cookies-parse-success = Successfully parsed with { $parser }
cookies-save-user-info = Saving user info to FeelUOwn data directory
cookies-loading-existing-user = Attempting to load existing user...

# feeluown.gui.widgets.table_toolbar
# ----------------------------------------
play-all-button = Play All
play-all-button-fetching = Fetching all songs...
play-all-button-fetch-done = {play-all-button-fetching} done

album-filter-all = All { -album }s
album-filter-standard = Standard
album-filter-singular-or-ep = Singles & EPs
album-filter-live = Live
album-filter-compilation-retrospective = Compilation/Retrospective

# feeluown.gui.widgets.songs
# ----------------------------------------
add-to-playlist = Add to playlist
remove-from-playlist = Remove { -track }

# feeluown.gui.uimain
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.uimain.playlist_overlay
# ----------------------------------------
playlist-clear = Clear { playlist }
jump-to-playing-track = Current { -track }
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
similar-tracks = Similar{ -track }
track-hot-comments = Hot comments
movie-mode-exit = Exit movie mode

# feeluown.gui.uimain.sidebar
# ----------------------------------------
-local-favorites = Local favorites
local-favorites = { -local-favorites }

collections-header-tooltip =
    You can create ‘{ -track-collection }s’ locally to save your favorite music resources

    Each { -track-collection } exists as an independent .fuo file. Hover over a { -track-collection } to view its file path.
    Creating a new .fuo file creates a new { -track-collection }; the filename is the { -track-collection }’s name.

    You can manually edit the .fuo file to edit the music resources in the { -track-collection },
    or drag and drop {-track}s in the interface to add or remove them.
ai-configure-tooltip =
    You need to install the Python third-party library openai,
    and configure the following settings to use the AI assistant
    config.OPENAI_API_KEY = sk-xxx
    config.OPENAI_API_BASEURL = http://xxx
    config.OPENAI_API_MODEL = model name

collection-id = ID
collection-title = Title

## collectionName: [string] title/name of the collection
collection-already-exists = { -track-collection(capitalization: "uppercase") } '{ $collectionName }' already exists
collection-confirm-remove = Confirm to delete the collection '{ $collectionName }'?

# feeluown.gui.uimain.provider_bar
# ----------------------------------------
my-favorite-button = { my-favorite-title }
my-playlists = { track-list }s
my-tracks = My tracks
provider-unknown-tooltip = Unknown provider
fold-top-tooltip = { fold-collapse }/{ fold-expand } Homepage and { -local-favorites }

## providerName: [string] name of the provider

provider-recommended-page-enter = Recommendation of { $providerName }
provider-custom-ui-missing = Provider didn't register their UI

## Note: this can also be due to missing of logged user

playlist-create-unsupported = Provider cannot create {track-list}s yet

## providerName: [string] name of the provider

playlist-remove-unsupported = Provider { $providerName } doesn't support removing playlist

## playlistTitle: [string]
## errorMessage: [string]

playlist-create-succed = Created { track-list } '{ $playlistTitle }'
playlist-create-failed = Failed to create { track-list } '{ $playlistTitle }': { $errorMessage }
playlist-remove-succed = Removed { track-list } '{ $playlistTitle }'
playlist-remove-failed = Failed to remove { track-list } '{ $playlistTitle }'
playlist-remove-confirm = Confirm to remove '{ $playlistTitle }'?
playlist-name = { track-list } Name
# feeluown.gui.pages.song_explore
# ----------------------------------------
track-lyrics = Lyrics
track-start-play = Play
track-webpage-url-copy = Copy webpage URL
track-belongs-album = { -album(capitalization: "uppercase") }
release-date = Release date
track-genre = Genre
error-message-template =
    <p style=color: grey; font: small;>This provider does not yet support{ "{" }feature{ "}" }.
    <br/> Implement the { $interface } interface to support this feature ~
    </p>
find-similar-tracks = View{ similar-tracks }
track-view-comments = View{ -track } comments

# feelown.gui.pages
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.pages.coll_mixed
# ----------------------------------------
-music-library = Music Library
music-library = { -music-library }

music-library-empty = { -music-library } has no content yet, go add some!
collection-is-empty = This { -track-collection } has no content yet, go add some!

## item: [string]
remove-item-succeed = Removed { $item } successfully

# feeluown.gui.pages.homepage
# ----------------------------------------
fold-expand = Expand
fold-collapse = Collapse
fold-tooltip = { fold-expand }/{ fold-collapse }
recommended-playlist = Recommended { track-list }s
recommended-daily-playlist = Daily Mixes
recommended-feelin-lucky = Just listening
recommended-videos = Take a look
recommended-videos-missing = No recommended { video }

# feeluown.gui.pages.my_fav.py
# ----------------------------------------


## providerName: [string] name of the provider
## mediaType: [string] can be one of:
##    track
##    album
##    singer
##    playlist
##    video

provider-missing-favorite =
    Provider { $providerName } doesn't support Liked { $mediaType ->
        [track] { -track }
        [album] { album }
        [singer] { musician }
        [playlist] { track-list }
        [video] { video }
       *[other] Contents
    }
provider-unknown-cannot-view = Provider unknown, cannot view this page
my-favorite-title = My favorites

# feeluown.gui.pages.recommendation
# ----------------------------------------
music-blacklisted = Musics blacklisted

## Similar to Spotify Radio
-music-radio-radar = Music Radio
music-radio-radar = { -music-radio-radar }
music-radio-radar-activated = { -music-radio-radar } activated
## Generate Radio stream based on the new track
music-radio-radar-changed = { -music-radio-radar } switched
## Find music recommendations
music-discovery = Discover Music
## Similar to Spotify Discover Weekly
music-customized-recommendation = Discover Weekly

