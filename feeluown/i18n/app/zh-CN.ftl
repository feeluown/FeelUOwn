### Locallication for FeelUOwn

# Common translation
# This is for common buttons, like:
# minimize, fullscreen, close, e.g.
# ----------------------------------------
minimize-window = 最小化
fullscreen-window = 窗口全屏
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

# feeluown.version
# ----------------------------------------
new-version-found = 检测到新版本 { $latestVer }，当前版本为 { $currentVer }
already-updated = 当前已经是最新版本: { $latestVer }

# feeluown.local
# ----------------------------------------
local-tracks-scan-finished = 本地音乐扫描完毕
# feeluown.local.provider
# ----------------------------------------
local-tracks = 本地音乐

# feeluown.gui.tips
# ----------------------------------------

tips-osdlyrics = 你知道 FeelUOwn 可以配合 osdlyrics 使用吗?
tips-show-more-tips = 在搜索框输入“>>> app.tips_mgr.show_random()”查看更多 Tips
tips-album-original-image = 专辑图片上右键可以查看原图哦 ~
tips-track-drag-to-playlist = 可以拖动{ track }来将{ track }添加到歌单呐！
tips-common-tooltip = 鼠标悬浮或右键常有惊喜 ~
tips-watch-mode = 开启 watch 模式一边看 MV，一边工作学习香不香？

## shortcut: the shortcut key
tips-search-shortcut = 搜索快捷键是 { $shortcut }

## note: $user is passed with prefix '@'
thanks-contributor = 感谢 { $user } 的贡献 :)

# feeluown.gui.watch
# ----------------------------------------
picture-in-picture = 画中画
hide-picture-in-picture = 退出{ picture-in-picture }

# feeluown.gui.components
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.components.avatar
# ----------------------------------------
login-third-party = 点击登录第三方平台
some-platform-already-logged = 已登录部分平台
switch-third-party-account = 切换账号

switch-music-platform = 点击切换平台

## platforms: providers' name conjucted by a comma
## platformsCount: amount of logged providers
logged-accounts-tooltip = 后台已登录：{ $platformsCount ->
    [0] 无
    *[other] { $platforms }
}

# feeluown.gui.components.btns
# ----------------------------------------
lyric-button = 词
watch-mode-tooltip =
    开启 watch 模式时，播放器会优先尝试为{ track }找一个合适的{ video }来播放。
    最佳实践：开启 watch 的同时建议开启{ video }的{ picture-in-picture }模式。

local-liked-tracks = “本地收藏”
local-liked-tracks-add = 添加到{ local-liked-tracks }
local-liked-tracks-remove = 从{ local-liked-tracks }中移除
local-liked-tracks-added = 已添加到{ local-liked-tracks }
local-liked-tracks-removed = 已从{ local-liked-tracks }移除

show-track-movie = 展示{ video }画面

# feeluown.gui.components.collections
# ----------------------------------------
track-collection = 收藏集
remove-this-collection = 删除此{ track-collection }

# feeluown.gui.components.line_song
# ----------------------------------------
play-stage-prepare-track-url = 正在获取{track}播放链接...
play-stage-prepare-track-url-fallback = 尝试寻找备用播放链接...
play-stage-prepare-track-metadata = 尝试获取完整的{ track }元信息...
play-stage-prepare-track-loading = 正在加载{track}资源...
play-stage-prepare-movie-url = 正在获取音乐的{video}播放链接...

# feeluown.gui.components.menu
# ----------------------------------------
play-track-movie = 播放 MV
track-missing-album = 该{ track }没有{ album }信息
track-missing-movie = 该{ track }无 MV
track-search-similar = 搜索相似资源
track-show-artist = 查看{ musician }
track-show-album = 查看{ album }
track-enter-radio = { track }电台
track-show-detail = { track }详情

track-playlist-add = 加入到{ playlist }
track-playlist-add-succ = 已加入到{ $playlistName }✅
track-playlist-add-fail = 加入到{ $playlistName } 失败 ❌

track-movie-missing = 该{ track }无 MV

menu-ai-prompt =
    你是一个音乐播放器助手。
    【填入你的需求】
    { track }信息如下 -> { track }名：{ $songTitle }, 歌手名：{ $songArtists }
menu-ai-button = AI
menu-ai-copy-prompt = 复制 AI Prompt
menu-ai-copy-prompt-succeed = 已经复制到剪贴板

# feeluown.gui.components.nowplaying
# ----------------------------------------
track-movie-play-tooltip = 播放{ track }MV
track-album-release-date = 专辑{ release-date }：{ $releaseDate }

# feeluown.gui.components.player_playlist
# ----------------------------------------
fm-radio-current-song-dislike = 不想听
track-playlist-remove = 从{ playlist }中移除

track-provider-blacklist-add = 加入资源提供方的黑名单
track-provider-blacklist-adding = 正在加入黑名单，请稍等...
track-provider-blacklist-add-succ = 已加入黑名单
track-provider-blacklist-add-fail = 加入黑名单失败

track-radio-mode-remove-latest = FM 模式下，如果当前{ track }是最后一首歌，则无法移除。请稍后再尝试移除

# feeluown.gui.components.playlist_btn
# ----------------------------------------
playlist-show = 显示当前{ playlist }

# feeluown.gui.components.search
# ----------------------------------------

track-search = 搜索“{ $keyword }”

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

# feeluown.gui.widgets
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.widgets.labels
# ----------------------------------------
error-message-prefix = 错误：
info-message-prefix = 提示：

# feeluown.gui.widgets.selfpaint_btn
# ----------------------------------------
discovery = 发现
homepage = 主页
calender = 日历
top-list = 排行榜
favorites = 收藏
hot = 热门
emoji-expression = 表情

# feeluown.gui.widgets.magicbox
# ----------------------------------------
search-box-placeholder = 搜索{ track }、歌手、专辑、用户
search-box-tooltip =
    直接输入文字可以进行过滤，按 Enter 可以搜索
    输入 >>> 前缀之后，可以执行 Python 代码
    输入 “==> 执迷不悔 | 王菲”，可以直接播放{ track }
    输入 “=== 下雨天听点啥？”，可以和 AI 互动
    输入 # 前缀之后，可以过滤表格内容
    输入 > 前缀可以执行 fuo 命令（未实现，欢迎 PR）
search-box-ai-chat-unavailable = AI 聊天功能不可用
search-box-play-track = 尝试播放：{ $song }
search-box-play-track-ill-formed = 你输入的内容需要符合格式：“{ track }标题 | 歌手名”

# feeluown.gui.widgets.settings
# ----------------------------------------
app-config = 应用配置
save-config = 保存
search-providers = 搜索来源
ai-radio-prompt = AI 电台 (提示词)
player = 播放器

# feeluown.gui.widgets.login
# ----------------------------------------
cookies-dialog-login-button  = 登录
cookies-dialog-web-login-btn = 使用 FeelUOwn 内置浏览器登录
cookies-dialog-chrome-btn    = 从 Chrome 中读取 Cookie
cookies-dialog-firefox-btn   = 从 Firefox 中读取 Cookie
cookies-dialog-edge-btn      = 从 Edge 中读取 Cookie

cookies-dialog-tutorial =
    FeelUOwn 提供了几种登录第三方音乐平台的方式，
    <span style='color:red'>任选一种即可</span>。<br/><br/>
    如果你已经在常用浏览器上登录了第三方平台，可以优先选择“读取 Cookie”方式登录。
    其它情况，推荐使用“{ cookies-dialog-web-login-btn }”方式登录（你需要安装 pyqt webengine 才可使用）。
    当然，如果你知道如何手动拷贝 Cookie，你可以先拷贝 Cookie，然后点击“登录”。

cookies-dialog-placeholder =
    请从浏览器中复制 Cookie！

    你可以拷贝一个请求的 Cookie Header，格式类似 key1=value1; key2=value2
    你也可以填入 JSON 格式的 Cookie 内容，类似 {"{"}"key1": "value1", "key2": "value2"{"}"}

cookies-parse-fail    = 使用 { $parser } 解析器解析失败，尝试下一种
cookies-parse-success = 使用 { $parser } 解析器解析成功

cookies-save-user-info        = 保存用户信息到 FeelUOwn 数据目录
cookies-loading-existing-user = 正在尝试加载已有用户...

# feeluown.gui.widgets.songs
# ----------------------------------------
add-to-playlist = 添加到播放队列
remove-from-playlist = 移除{ track }

# feeluown.gui.uimain
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.uimain.playlist_overlay
# ----------------------------------------
playlist-clear = 清空{ playlist }
jump-to-playing-track = 跳转到当前{ track }

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

# feeluown.gui.uimain.nowplaying_overlay
# ----------------------------------------
similar-tracks = 相似{track}
track-hot-comments = 热门评论
movie-mode-exit = 退出视频模式

# feeluown.gui.pages.song_explore
# ----------------------------------------
track-lyrics = 歌词
track-start-play = 播放
track-webpage-url-copy = 复制网页地址
track-belongs-album = 所属专辑
release-date = 发行日期
track-genre = 曲风

error-message-template =
    <p style=color: grey; font: small;>该提供方暂不支持{"{"}feature{"}"}。
    <br/> 给它实现一下 { $interface } 接口来支持该功能吧 ~
    </p>
find-similar-tracks = 查看{ similar-tracks }
track-view-comments = 查看{ track }评论

# feelown.gui.pages
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.pages.homepage
# ----------------------------------------
fold-expand = 展开
fold-collapse = 收起
fold-tooltip = {fold-expand}/{fold-collapse}

recommended-playlist = 推荐{track-list}
recommended-daily-playlist = 每日推荐
recommended-feelin-lucky = 随便听听
recommended-videos = 瞅瞅
recommended-videos-missing = 暂无推荐{video}

# feeluown.gui.pages.my_fav.py
# ----------------------------------------

## providerName: [string] name of the provider
## mediaType: [string] can be one of:
##    track
##    album
##    singer
##    playlist
##    video
provider-missing-favorite = 当前资源提供方（{ $providerName }）不支持获取 收藏的{ $mediaType ->
    [track] {track}
    [album] {album}
    [singer] {musician}
    [playlist] {track-list}
    [video] {video}
   *[other] 内容
}
provider-unknown-cannot-view = 当前资源提供方未知，无法浏览该页面
my-favorite-title = 我的收藏
