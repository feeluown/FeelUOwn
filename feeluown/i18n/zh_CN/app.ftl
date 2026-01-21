### Locallication for FeelUOwn

# Common translation
# This is for common buttons, like:
# minimize, fullscreen, close, e.g.
# ----------------------------------------
minimize-window = 最小化
fullscreen-window = 全屏
playlist = 播放列表
recently-played = 最近播放

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

# Version info (feeluown.version)
# ----------------------------------------
new-version-found = 检测到新版本 { $latestVer }，当前版本为 { $currentVer }
already-updated = 当前已经是最新版本: { $latestVer }

# Local musics (feeluown.local)
# ----------------------------------------
local-tracks-scan-finished = 本地音乐扫描完毕
# Local musics (feeluown.local.provider)
# ----------------------------------------
local-tracks = 本地音乐

# Tips banner (feeluown.gui.tips)
# ----------------------------------------

tips-osdlyrics = 你知道 FeelUOwn 可以配合 osdlyrics 使用吗?
tips-show-more-tips = 在搜索框输入“>>> app.tips_mgr.show_random()”查看更多 Tips
tips-album-original-image = 专辑图片上右键可以查看原图哦 ~
tips-track-drag-to-playlist = 可以拖动歌曲来将歌曲添加到歌单呐！
tips-common-tooltip = 鼠标悬浮或右键常有惊喜 ~
tips-watch-mode = 开启 watch 模式一边看 MV，一边工作学习香不香？

## shortcut: the shortcut key
tips-search-shortcut = 搜索快捷键是 { $shortcut }

## note: $user is passed with prefix '@'
thanks-contributor = 感谢 { $user } 的贡献 :)

# Watch mode (feeluown.gui.watch)
# ----------------------------------------
picture-in-picture = 画中画
hide-picture-in-picture = 退出{ picture-in-picture }

# COMPONENTS
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Avatar component (feeluown.gui.components.avatar)
# ----------------------------------------
login-third-party = 点击登录第三方平台
some-platform-already-logged = 已登录部分平台
switch-third-party-account = 切换账号

switch-music-platform = 点击切换平台

logged-accounts-tooltip = 后台已登录：{ $platformsCount ->
    [0] 无
    *[other] { $platforms }
}

# Buttons component (feeluown.gui.components.btns)
# ----------------------------------------
lyric-button = 词
watch-mode-tooltip =
    开启 watch 模式时，播放器会优先尝试为{ track }找一个合适的{ video }来播放。
    最佳实践：开启 watch 的同时建议开启{ video }的{ picture-in-picture }模式。

local-liked-tracks = “本地收藏”
local-liked-tracks-add = 添加到{ local-liked-tracks }
local-liked-tracks-remove = 从{ local-liked-tracks }中移除
local-liked-tracks-added = 已经{ local-liked-tracks-add }
local-liked-tracks-removed = 已经{ local-liked-tracks-remove }

show-track-movie = 展示{ video }画面

# Collections component (feeluown.gui.components.collections)
# ----------------------------------------
track-collection = 收藏集
remove-this-collection = 删除此{ track-collection }

# Song status line component (feeluown.gui.components.line_song)
# ----------------------------------------
play-stage-prepare-track-url = 正在获取{track}播放链接...
play-stage-prepare-track-url-fallback = 尝试寻找备用播放链接...
play-stage-prepare-track-metadata = 尝试获取完整的歌曲元信息...
play-stage-prepare-track-loading = 正在加载{track}资源...
play-stage-prepare-movie-url = 正在获取音乐的{video}播放链接...

# Menu component (feeluown.gui.components.menu)
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

# Nowplaying component (feeluown.gui.components.nowplaying)
# ----------------------------------------
track-movie-play-tooltip = 播放{ track }MV
track-album-release-date = 专辑发行日期：{ $releaseDate }

# Player playlist component (feeluown.gui.components.player_playlist)
# ----------------------------------------
fm-radio-current-song-dislike = 不想听
track-playlist-remove = 从{ playlist }中移除

track-provider-blacklist-add = 加入资源提供方的黑名单
track-provider-blacklist-adding = 正在加入黑名单，请稍等...
track-provider-blacklist-add-fail = 加入黑名单失败

# Playlist button component (feeluown.gui.components.playlist_btn)
# ----------------------------------------
playlist-show = 显示当前{ playlist }

# Track search component (feeluown.gui.components.search)
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

# WIDGETS
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Self paint buttons (feeluown.gui.widgets.selfpaint_btn)
# ----------------------------------------
discovery = 发现
homepage = 主页
calender = 日历
top-list = 排行榜
favorites = 收藏
hot = 热门
emoji-expression = 表情

# UIMAIN
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

## feeluown.gui.uimain.playlist_overlay
# ----------------------------------------
playlist-clear = 清空{ playlist }
jump-to-playing-track = 跳转到当前歌曲

song-radio-mode = 自动续歌
song-radio-mode-empty-playlist = 播放队列为空，不能激活“{ song-radio-mode }”功能
song-radio-mode-activated = “{ song-radio-mode }”功能已激活

playback-mode = 播放模式
playback-mode-change = 修改{ playback-mode }
playback-mode-single-repeat = 单曲循环
## play songs in original order, on end stop playing
playback-mode-sequential = 顺序播放
## play songs in original order, on end back to the first
playback-mode-loop = 循环播放
## play songs in random order
playback-mode-random = 随机播放