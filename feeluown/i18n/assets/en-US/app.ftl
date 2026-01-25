### Locallication for FeelUOwn

# Common translation
# This is for common buttons, like:
# minimize, fullscreen, close, e.g.
# ----------------------------------------
minimize-window = Minimize
fullscreen-window = Full Screen
playlist = Playlist
recently-played = Recently Played
unknown = Unknown
description = Description

-error = Error
-info = Note
-warn = Warning
error = { -error }
info = { -info }
warn = { -warn }

## Resource provider, like ytmusic, spotify, e.g.
-provider = { $capitalization ->
    [uppercase] { $plural ->
        [plural] Providers
       *[singular] Provider
    }
   *[lowercase] { $plural ->
        [plural] providers
       *[singular] provider
    }
}

# Tab name, commonly used
# ----------------------------------------
-track = { $capitalization ->
    [uppercase] Trac
   *[lowercase] trac
}{ $plural ->
    [plural] ks
    *[singular] k
}
track = { -track(capitalization: "uppercase") }

## Note: this is for playlists from online providers
## while { playlist } is for tracks play queue.
-track-list = { $plural ->
    [plural] Playlists
   *[singular] Playlist
}
track-list = { -track-list }

-album = { $capitalization ->
    [uppercase] Album
   *[lowercase] album
}
album = { -album(capitalization: "uppercase") }
video = Video

## can be the singer, artist, or musician.
-musician = { $capitalization ->
    [uppercase] Musician
   *[lowercase] musician
}
musician = { -musician(capitalization: "uppercase") }

# feeluown.alert
# ----------------------------------------

## hostname: [string] hostname of the URL, or 'none'
connection-timeout = { $hostname ->
    [none] Connection timeout
    *[other] Connection to '{ $hostname }' timeout
}, please check your network/proxy settings!

## hostname: [string] hostname of the URL
## proxy: [string] the HTTP proxy URL or 'none'
media-loading-failed =
    Cannot play resource from { $hostname }, { $proxy ->
    [none] HTTP Proxy unset
    *[others] HTTP Proxy: {$proxy}
} (Tip: Player engine doesn't respect system proxy)

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
add-profile = Add profile
select-profile = Select profile
switch-profile = Switch profile

## profiles: profiles' name conjucted by a comma
## profileCount: amount of profiles

profiles-tooltip =
    Profiles: { $profileCount ->
        [0] None
       *[other] { $profiles }
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
play-stage-prepare-track-url-fallback = Trying to find a fallback playback URL...
play-stage-prepare-track-metadata = Trying to fetch complete { -track } metadata...
play-stage-prepare-track-loading = Loading { -track } resources...
play-stage-prepare-movie-url = Obtaining { video } playback URL for the music...
# feeluown.gui.components.menu
# ----------------------------------------
play-track-movie = Play MV
track-missing-album = No { album } information for this { -track }
track-missing-movie = { -track(capitalization: "uppercase") } has no MV
track-search-similar = Search for similar resources
track-show-artist = View { musician }
track-show-album = View { album }
track-enter-radio = { -track(capitalization: "uppercase") } Radio
track-show-detail = { -track(capitalization: "uppercase") } Details
track-playlist-add = Add to { -track-list }
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
track-album-release-date = { -album(capitalization: "uppercase") } { release-date }: { $releaseDate }
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

track-searching = Searching { $providerCount } content { -provider(plural: "plural") }...

## providerName: name of the content provider

track-search-error = Error searching from { $providerName }: { $errorMessage }
track-search-result-empty = Searching { $providerName } yielded no results

## resultCount: amount of valid results
## timeCost: seconds cost for searching, floating number
## See https://projectfluent.org/fluent/guide/selectors.html
track-search-done = Search completed, with { $resultCount ->
    [one] { $resultCount } valid result
    *[other] { $resultCount } valid results
}, taking { NUMBER($timeCost, minimumFractionDigits: 2, maximumFractionDigits: 2) }s

# feeluown.gui.components.song_tag
# ----------------------------------------
# This is for missing track fallback,
# when you cannot play original track due to copyright issues, e.g.

music-source = Music source
track-smart-standby = Smart Standby
track-unknown-source = Unknown source

track-fallback-to-standby = Used { $standby } to replace the current { -track }
track-fallback-failed = { -provider(capitalization: "uppercase") } “{ $providerName }” did not find any similar { -track }s available

# feeluown.gui.widgets
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.widgets.ai_chat
# ----------------------------------------
ai-chat-input-placeholder = Chat with the assistant
ai-chat-send-button = Send

# feeluown.gui.widgets.cover_label
# ----------------------------------------
show-original-image = Show original

# feeluown.gui.widgets.img_card_list
# ----------------------------------------
remove-action = Remove
remove-action-video = { remove-action } Movie
remove-action-playlist = { remove-action } { -track-list }
remove-action-musician = { remove-action } { -musician }
remove-action-album = { remove-action } { -album }

## releaseDate: [date, datetime] datetime when album was published
## trackCount: [int] amount of tracks in this album
album-release-date = { $trackCount ->
    [0] { DATETIME($releaseDate, year: "numeric", day: "numeric", month: "short") }
    [1] { DATETIME($releaseDate, year: "numeric", day: "numeric", month: "short") } { $trackCount } song
    *[other] { DATETIME($releaseDate, year: "numeric", day: "numeric", month: "short") } { $trackCount } songs
}

# feeluown.gui.widgets.labels
# ----------------------------------------
error-message-prefix = { -error }:{ " " }
info-message-prefix = { -info }:{ " " }
# feeluown.gui.widgets.selfpaint_btn
# ----------------------------------------
configuration-button = Configuration
discovery = Discovery
homepage = Home
calender = Calender
top-list = Top list
favorites = Favorites
hot = Hot
emoji-expression = Emoji

# feeluown.gui.widgets.volume_button
# ----------------------------------------
volume-button-tooltip = Adjust volume

# feeluown.gui.widgets.playlists
# ----------------------------------------
track-list-remove = Remove this { -track-list }

# status: [string], 'succ' for success, 'fail' for failure
playlist-add-track = Add { -track } to { playlist }{ $status ->
    [succ] succeed
   *[fail] failed
}

# feeluown.gui.widgets.provider
# ----------------------------------------
logged = Logged-in

# feeluown.gui.widgets.progress_slider
# ----------------------------------------
drag-to-seek-progress = Drag to seek

# feeluown.gui.widgets.songs
# ----------------------------------------
track-source = Source
track-duration = Duration

# feeluown.gui.widgets.tabbar
# ----------------------------------------

## Albums containting this track
track-contributed-albums = Contributed works

# feeluown.gui.widgets.magicbox
# ----------------------------------------
search-box-placeholder = Search { -track }s, artists, { -album }s, users
search-box-tooltip =
    Type text directly to filter, press Enter to search
        Input >>> prefix to execute Python code
        Input "==> Playing Without Regret | Faye Wong" to play a { -track } directly
        Input "=== What to listen on a rainy day?" to interact with AI
        Input # prefix to filter table content
        Input > prefix to execute fuo command (not implemented, PR welcome)
search-box-ai-chat-unavailable = AI chat is unavailable
search-box-play-track = Try to play: { $song }
search-box-play-track-ill-formed = Your input must follow the format: "{ -track } title | Artist name"
# feeluown.gui.widgets.settings
# ----------------------------------------
app-config = App Configuration
save-config = Save
search-providers = Search { -provider(capitalization: "uppercase") }s
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
cookies-loading-existing-user = Trying to load existing user...

# feeluown.gui.widgets.table_toolbar
# ----------------------------------------
play-all-button = Play All
play-all-button-fetching = Fetching all songs...
play-all-button-fetch-done = { play-all-button-fetching } done

album-filter-all = All { -album }s
album-filter-standard = Standard
album-filter-singular-or-ep = Singles & EPs
album-filter-live = Live
album-filter-compilation-retrospective = Compilation/Retrospective

# feeluown.gui.widgets.meta
# ----------------------------------------

## dateTime: [date, datetime]
## https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat
meta-created-at =
    🕛 Created at
    <code style="font-size: medium">
        { DATETIME($dateTime, year: "numeric", day: "numeric", month: "short") }
    </code>
meta-updated-at =
    🕛 Updated at
    <code style="font-size: medium">
        { DATETIME($dateTime, year: "numeric", day: "numeric", month: "short") }
    </code>
meta-released-at =
    🕛 Released at
    <code style="font-size: medium">
        { DATETIME($dateTime, year: "numeric", day: "numeric", month: "short") }
    </code>

## songsCount: [int] number of songs, -1 for unknown
meta-amount-songs = { $songsCount ->
    [-1] Unknown
    [0] No songs
    *[other] <code style="font-size: medium">{ $songsCount }</code> songs
}

# feeluown.gui.widgets.songs
# ----------------------------------------
add-to-playlist = Add to playlist
remove-from-playlist = Remove { -track }

# feeluown.gui.uimain
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.uimain.ai_chat
# ----------------------------------------
ai-chat-header = AI Assistant
ai-chat-new = New chat
ai-chat-match-resource = Matching resources...
ai-chat-match-resource-failed = Resource matching failed
ai-chat-track-candidate-list = { -track(capitalization: "uppercase") } candidate list

# feeluown.gui.uimain.player_bar
# ----------------------------------------
## released: [string]
album-released-at = { -album(capitalization: "uppercase") } released at: { $released }

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

# feeluown.gui.uimain.lyric
# ----------------------------------------
lyric-not-available = Lyrics not available
lyric-background-color = Background color
lyric-text-color = Text color
lyric-font = Font
lyric-show-bilingual = Bilingual lyrics
lyric-window-auto-resize = Auto resize

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
    or drag and drop { -track }s in the interface to add or remove them.
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
collection-confirm-remove = Confirm to delete the { -track-collection } '{ $collectionName }'?

# feeluown.gui.uimain.toolbar
# ----------------------------------------
-search-bar = Search Bar
search-bar-show = Show { -search-bar }
search-bar-hide = Hide { -search-bar }

# feeluown.gui.uimain.provider_bar
# ----------------------------------------
my-favorite-button = { my-favorite-title }
my-playlists = { -track-list }s
my-tracks = My tracks
provider-unknown-tooltip = Unknown provider
fold-top-tooltip = { fold-collapse }/{ fold-expand } Homepage and { -local-favorites }

## providerName: [string] name of the provider

provider-recommended-page-enter = Recommendation of { $providerName }
provider-custom-ui-missing = { -provider(capitalization: "uppercase") } didn't register their UI

## Note: this can also be due to missing of logged user

playlist-create-unsupported = { -provider(capitalization: "uppercase") } cannot create { -track-list }s yet

## providerName: [string] name of the provider

playlist-remove-unsupported = { -provider(capitalization: "uppercase") } { $providerName } doesn't support removing playlist

## playlistTitle: [string]
## errorMessage: [string]

playlist-create-succed = Created { -track-list } '{ $playlistTitle }'
playlist-create-failed = Failed to create { -track-list } '{ $playlistTitle }': { $errorMessage }
playlist-remove-succed = Removed { -track-list } '{ $playlistTitle }'
playlist-remove-failed = Failed to remove { -track-list } '{ $playlistTitle }'
playlist-remove-confirm = Confirm to remove '{ $playlistTitle }'?
playlist-name = { -track-list } Name
# feeluown.gui.pages.song_explore
# ----------------------------------------
track-lyrics = Lyrics
track-start-play = Play
track-webpage-url-copy = Copy webpage URL
track-belongs-album = { -album(capitalization: "uppercase") }
release-date = Release date
track-genre = Genre

## url: [string]
track-webpage-url-copied = Copied: { $url }

## providerName: [string]
## This happens if user uninstalled a plugin, or modified
## their collections by hand, e.g.
track-source-provider-missing = { -provider(capitalization: "uppercase") } { $providerName } not found

error-message-template =
    <p style="color: grey; font: small;">This provider does not yet support { "{" }feature{ "}" }.
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
recommended-playlist = Made for You
recommended-daily-playlist = Daily Mixes
recommended-feelin-lucky = Just listening
recommended-videos = Take a look
recommended-videos-missing = No recommended { video }

# feeluown.gui.pages.my_dislike
# ----------------------------------------

## providerName: [string] name of the provider
## resType: [string] 'unknown', 'dislike'
provider-unsupported = { -provider(capitalization: "uppercase") } { $providerName} does not support displaying { $resType ->
    [dislike] Disliked { -track(plural: "plural") }
    *[unknown] Unknown resource type
}

# feeluown.gui.pages.my_fav
# ----------------------------------------

## providerName: [string] name of the provider
## mediaType: [string] can be one of:
##    track
##    album
##    singer
##    playlist
##    video

provider-missing-favorite =
    { -provider(capitalization: "uppercase") } { $providerName } doesn't support Liked { $mediaType ->
        [track] { -track }
        [album] { album }
        [singer] { musician }
        [playlist] { -track-list }
        [video] { video }
       *[other] Contents
    }
provider-unknown-cannot-view = { -provider(capitalization: "uppercase") } unknown, cannot view this page
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

# feeluown.gui.pages.model
# ----------------------------------------
provider-unsupported-fetch-artist-contributed-works =
    { -provider(capitalization: "uppercase") } does not support obtaining { -album } contributed by { -musician }
provider-unsupported-fetch-artist-works =
    { -provider(capitalization: "uppercase") } does not support obtaining { -album } for { -musician }
provider-unsupported-fetch-artist = { -provider(capitalization: "uppercase") } does not support obtaining { -track } for { -musician }
provider-unsupported-fetch-album = { -provider(capitalization: "uppercase") } does not support obtaining { -track } for { -album }
provider-unsupported-fetch-playlist = { -provider(capitalization: "uppercase") } does not support obtaining { -track } for { -track-list }s

# feeluown.gui.pages.provider_home
# ----------------------------------------
provider-liked-music = Liked
provider-playlist-list = { -track-list(plural: "plural") }

# feeluown.gui.pages.toplist
# ----------------------------------------
# ref: provider-unknown-cannot-view
# ref: top-list

## songTitle: [string]
track-playlist-remove-succ = Removed { -track } { $songTitle } successfully
track-playlist-remove-fail = Failed to remove { -track } { $songTitle }

# feeluown.gui.tray
# ----------------------------------------

## action: [string] "show", "hide"
## Show and focus app main window after hide to tray
tray-main-window-action = { $action ->
    [show] Show
   *[hide] Hide
} Window

## action: [string] "play", "pause"
tray-toggle-playpause = { $action ->
    [pause] Pause
    *[play] Play
}

tray-skip-track-next = Next
tray-skip-track-prev = Previous

tray-quit-application = Quit

# feeluown.player
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.player.fm
# ----------------------------------------
track-radio-not-enough = No enough { -track(plural: "plural") }, exiting FM mode

# feeluown.player.playlist
# ----------------------------------------
## errorMessage: [string]
track-url-fetch-failed = Failed to fetch URL for { -track }: { $errorMessage }

-music-video = Music video
track-fallback-music-video = Using { -music-video } as its playback source ✅
track-fallback-no-music-video = No available { -music-video } resource found 🙁

music-video-not-avaliable = No available { -music-video } resource found

playback-url-unavailable = No available playback URL

## standby: [string] standby provider for this resource
## track: the target track to play
track-standby-try = No available playback resources for { $track }, trying to find a stand-by { -track }...
track-standby-found = Found a stand-by { -track } for { $track } on { $standby } ✅
track-standby-unavailable = No stand-by { -track } found for { $track }

track-skip-to-next = No available playback link found, playing the next...

# feeluown.gui.page_containers
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.page_containers.table
# ----------------------------------------

## errorMessage: [string]
provider-missing-feature = { -provider(capitalization: "uppercase") } does not support this feature: { $errorMessage }
provider-network-error = Request failed: { $errorMessage }