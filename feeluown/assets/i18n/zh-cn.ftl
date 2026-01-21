### Locallication for FeelUOwn

# Common translation
# This is for common buttons, like:
# minimize, fullscreen, close, e.g.
# ----------------------------------------
minimize-window = 最小化
playlist = 播放列表

# Tab name, commonly used
# ----------------------------------------
track = 歌曲
## Note: this is for playlists from online providers
## while {playlist} is for tracks play queue.
track-list = 歌单
album = 专辑
video = 视频

## can be the singer, artist, or musician.
musician = 歌手

# Tips banner
# ----------------------------------------

tips-osdlyrics = 你知道 FeelUOwn 可以配合 osdlyrics 使用吗?
tips-search-shortcut = 搜索快捷键是 Ctrl + F
tips-show-more-tips = 在搜索框输入“>>> app.tips_mgr.show_random()”查看更多 Tips
tips-album-original-image = 专辑图片上右键可以查看原图哦 ~
tips-common-tooltip = 鼠标悬浮或右键常有惊喜 ~
tips-watch-mode = 开启 watch 模式一边看 MV，一边工作学习香不香？

# note: $user is passed with prefix '@'
thanks-contributor = 感谢 { $user } 的贡献 :)

# Watch mode
# ----------------------------------------
picture-in-picture = 画中画
hide-picture-in-picture = 退出{ picture-in-picture }

# Avatar component
# ----------------------------------------
login-third-party = 点击登录第三方平台
some-platform-already-logged = 已登录部分平台
switch-third-party-account = 切换账号

switch-music-platform = 点击切换平台

## loggedUsers: user names conjucted by a comma
## loggedUsersCount: length of the user name list
logged-accounts-tooltip = 后台已登录：{ $loggedUsersCount ->
    [0] 无
    *[other] { $loggedUsers }
}

# Buttons component
# ----------------------------------------
lyric-button = 词
watch-mode-tooltip =
    开启 watch 模式时，播放器会优先尝试为{ track }找一个合适的{ video }来播放。
    最佳实践：开启 watch 的同时建议开启{ video }的{ picture-in-picture }模式。

local-liked-tracks = “本地收藏”
local-liked-tracks-add = 添加到{ local-liked-tracks }
local-liked-tracks-added = 已经{ local-liked-tracks-add }
local-liked-tracks-removed = 已经从{ local-liked-tracks }中移除

show-track-movie = 展示{ video }画面

# Collections component
# ----------------------------------------
track-collection = 收藏集
remove-this-collection = 删除此{ track-collection }

# Song status line component (line_song.py)
# ----------------------------------------
play-stage-prepare-track-url = 正在获取{track}播放链接...
play-stage-prepare-track-url-fallback = 尝试寻找备用播放链接...
play-stage-prepare-track-metadata = 尝试获取完整的歌曲元信息...
play-stage-prepare-track-loading = 正在加载{track}资源...
play-stage-prepare-movie-url = 正在获取音乐的{video}播放链接...

# Menu component (menu.py)
# ----------------------------------------
track-missing-album = 该{ track }没有{ album }信息
track-search-similar = 搜索相似资源
track-show-artist = 查看{ musician }
track-show-album = 查看{ album }
track-enter-radio = { track }电台
track-show-detail = { track }详情

track-playlist-add = 加入到{ playlist }
track-playlist-add-succ = 已加入到{ $playlistName }✅
track-playlist-add-fail = 加入到{ $playlistName } 失败 ❌

track-movie-missing = 该{ track }无 MV

menu-ai-button = AI
menu-ai-copy-prompt = 复制 AI Prompt
menu-ai-copy-prompt-succeed = 已经复制到剪贴板

# Nowplaying component (nowplaying.py)
# ----------------------------------------
track-movie-play-tooltip = 播放{ track }MV
track-album-release-date = 专辑发行日期：{ $releaseDate }

# Player playlist component (player_playlist.py)
# ----------------------------------------
fm-radio-current-song-dislike = 不想听
track-playlist-remove = 从{ playlist }中移除

track-provider-blacklist-add = 加入资源提供方的黑名单
track-provider-blacklist-adding = 正在加入黑名单，请稍等...
track-provider-blacklist-add-fail = 加入黑名单失败

# Playlist button component (playlist_btn.py)
# ----------------------------------------
playlist-show = 显示当前{ playlist }

# Track search component (search.py)
# ----------------------------------------

track-search = 搜索{ $keyword }

## providerCount: count of content providers.
track-searching = 正在搜索 { $providerCount }个资源提供方...

## providerName: name of the content provider
track-search-error = 搜索 { $providerName } 的资源出错：{ $errorMessage }
track-search-result-empty = 搜索 { $providerName } 的资源，提供方无结果

## resultCount: amount of valid results
## timeCost: seconds cost for searching, floating number
track-search-done = 搜索完成，共有 { $resultCount } 个有效的结果，花费 {
   NUMBER($timeCost, minimumFractionDigits: 2, maximumFractionDigits: 2)
}s
