### Locallication for FeelUOwn

# Common translation
# This is for common buttons, like:
# minimize, fullscreen, close, e.g.
# ----------------------------------------
minimize-window = Minimize
playlist = Playlist

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

# COMPONENTS
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Avatar component (avatar.py)
# ----------------------------------------
login-third-party = Login to a third-party platform
some-platform-already-logged = Already logged some platforms
switch-third-party-account = Change the account

switch-music-platform = Change the platform

## loggedUsers: user names conjucted by a comma
## loggedUsersCount: length of the user name list
logged-accounts-tooltip = Logged: { $loggedUsersCount ->
    [0] None
    *[other] { $loggedUsers }
}

# WIDGETS
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Widget selfpaint_btn.py
# ----------------------------------------
discovery = Discovery
homepage = Home
calender = Calender
top-list = Top list
favorites = Favorites
hot = Hot
emoji-expression = Emoji
