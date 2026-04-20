### Locallication for FeelUOwn

# Common translation
# This is for common buttons, like:
# minimize, fullscreen, close, e.g.
# ----------------------------------------
minimize-window = 最小化
fullscreen-window = ウィンドウ全画面
playlist = プレイリスト
recently-played = 最近再生
unknown = 不明
description = 説明

-error = エラー
-info = 情報
-warn = 警告
error = { -error }
info = { -info }
warn = { -warn }

## Resource provider, like ytmusic, spotify, e.g.
-provider = { $capitalization ->
   *[any] { $plural ->
       *[any] プロバイダー
    }
}

# Tab name, commonly used
# ----------------------------------------
-track = { $capitalization ->
   *[any] 曲
}
track = { -track }

## Note: this is for playlists from online providers
## while { playlist } is for tracks play queue.
-track-list = { $plural ->
   *[any] プレイリスト
}
track-list = { -track-list }

-album = { $capitalization ->
   *[any] アルバム
}
album = { -album }
video = ビデオ

## can be the singer, artist, or musician.
-musician = { $capitalization ->
   *[any] アーティスト
}
musician = { -musician }

# feeluown.alert
# ----------------------------------------

## hostname: [string] hostname of the URL, or 'none'
connection-timeout = { $hostname ->
    [none] 接続タイムアウト
    *[other] ホスト「{ $hostname }」への接続がタイムアウトしました
}、ネットワークまたはプロキシ設定を確認してください

## hostname: [string] hostname of the URL
## proxy: [string] the HTTP proxy URL or 'none'
media-loading-failed =
    { $hostname } からのメディアを再生できません、{ $proxy ->
    [none] HTTP プロキシが設定されていません
    *[others] HTTP プロキシ：{ $proxy }
}（注：再生エンジンはシステムプロキシを使用できません）

# feeluown.version
# ----------------------------------------
new-version-found = 新しいバージョン { $latestVer } が見つかりました。現在のバージョン：{ $currentVer }
already-updated = すでに最新バージョンです：{ $latestVer }

# feeluown.local
# ----------------------------------------
local-tracks-scan-finished = ローカル楽曲のスキャンが完了しました
# feeluown.local.provider
# ----------------------------------------
local-tracks = ローカル楽曲

# feeluown.gui.tips
# ----------------------------------------

tips-osdlyrics = FeelUOwn は osdlyrics と連携できますよ？
tips-show-more-tips = 検索ボックスに “>>> app.tips_mgr.show_random()” を入力するとさらに Tips が見られます
tips-album-original-image = { -album } の画像を右クリックすると原寸大を表示できます ~
tips-track-drag-to-playlist = { -track } をドラッグしてプレイリストに追加できます！
tips-common-tooltip = マウスオーバーや右クリックで思わぬ発見があるかも ~
tips-watch-mode = ウォッチモードをオンにすると MV を見ながら作業・勉強も捗りますよ！

## shortcut: the shortcut key
tips-search-shortcut = 検索ショートカットは { $shortcut }

## note: $user is passed with prefix '@'
thanks-contributor = { $user } さん、ご協力ありがとうございます :)

# feeluown.gui.watch
# ----------------------------------------
picture-in-picture = ピクチャーインピクチャー
hide-picture-in-picture = { picture-in-picture } を終了

# feeluown.gui.components
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.components.avatar
# ----------------------------------------
add-profile = プロフィールを追加
select-profile = プロフィールを選択
switch-profile = プロフィールを切り替え

## profiles: profiles' name conjucted by a comma
## profileCount: amount of profiles
profiles-tooltip = アカウント：{ $profileCount ->
    [0] なし
    *[other] { $profiles }
}

# feeluown.gui.components.btns
# ----------------------------------------
lyric-button = 歌詞
watch-mode-tooltip =
    ウォッチモードを有効にすると、プレイヤーはまず { -track } に合う { video } を探します。
    ベストプラクティス：ウォッチと同時に { video } の { picture-in-picture } モードもオンにしましょう。
fallback-button-tooltip = 代替ソースから検索できるようにする
local-liked-tracks = “ローカルお気に入り”
local-liked-tracks-add = { local-liked-tracks } に追加
local-liked-tracks-remove = { local-liked-tracks } から削除
local-liked-tracks-added = { local-liked-tracks } に追加しました
local-liked-tracks-removed = { local-liked-tracks } から削除しました

show-track-movie = { video } の映像を表示

# feeluown.gui.components.collections
# ----------------------------------------
-track-collection = { $capitalization ->
    [uppercase] コレクション
   *[lowercase] コレクション
}
track-collection = { -track-collection }
remove-this-collection = この { -track-collection } を削除

# feeluown.gui.components.line_song
# ----------------------------------------
play-stage-prepare-track-url = { -track } の再生リンクを取得中…
play-stage-prepare-track-url-fallback = 代替再生リンクを探しています…
play-stage-prepare-track-metadata = 完全な { -track } メタ情報を取得中…
play-stage-prepare-track-loading = { -track } のリソースを読み込み中…
play-stage-prepare-movie-url = 音楽の { video } 再生リンクを取得中…

# feeluown.gui.components.menu
# ----------------------------------------
play-track-movie = MV を再生
track-missing-album = この { -track } には { album } 情報がありません
track-missing-movie = この { -track } に MV はありません
track-search-similar = 類似リソースを検索
track-show-artist = { musician } を表示
track-show-album = { album } を表示
track-enter-radio = { -track } ラジオ
track-show-detail = { -track } の詳細

track-playlist-add = { -track } を { -track-list } に追加
track-playlist-add-succ = { $playlistName } に追加しました ✅
track-playlist-add-fail = { $playlistName } への追加に失敗 ❌

track-movie-missing = この { -track } に MV はありません

menu-ai-prompt =
    あなたは音楽プレーヤーアシスタントです。
    【ご要望を入力してください】
    { -track } の情報 -> 曲名：{ $songTitle }、アーティスト：{ $songArtists }
menu-ai-button = AI
menu-ai-copy-prompt = AI プロンプトをコピー
menu-ai-copy-prompt-succeed = クリップボードにコピーしました

# feeluown.gui.components.nowplaying
# ----------------------------------------
track-movie-play-tooltip = { -track } の MV を再生
track-album-release-date = { -album } 発売日：{ $releaseDate }

# feeluown.gui.components.player_playlist
# ----------------------------------------
fm-radio-current-song-dislike = 聞きたくない
track-playlist-remove = { playlist } から削除

track-provider-blacklist-add = { -provider } をブラックリストに追加
track-provider-blacklist-adding = ブラックリスト追加中…
track-provider-blacklist-add-succ = ブラックリストに追加しました
track-provider-blacklist-add-fail = ブラックリスト追加に失敗

track-radio-mode-remove-latest = FM モードでは、現在の { -track } が最後の一曲の場合、削除できません。後でもう一度お試しください

# feeluown.gui.components.playlist_btn
# ----------------------------------------
playlist-show = 現在の { playlist } を表示

# feeluown.gui.components.search
# ----------------------------------------

track-search = “{ $keyword }” を検索

## providerCount: count of content providers.
track-searching = { $providerCount } 個の { -provider } を検索中…

## providerName: name of the content provider
track-search-error = { $providerName } のリソース検索でエラー：{ $errorMessage }
track-search-result-empty = { $providerName } の検索で結果なし

## resultCount: amount of valid results
## timeCost: seconds cost for searching, floating number
track-search-done = 検索完了、有効な結果は { $resultCount } 件、所要時間 {
   NUMBER($timeCost, minimumFractionDigits: 2, maximumFractionDigits: 2)
}s

# feeluown.gui.components.song_tag
# ----------------------------------------
# This is for missing track fallback,
# when you cannot play original track due to copyright issues, e.g.

music-source = 音楽ソース
track-smart-standby = スマートスタンバイ
track-unknown-source = 不明なソース

track-fallback-to-standby = 現在の { -track } を { $standby } で置き換え
track-fallback-failed = プロバイダー “{ $providerName }” で利用可能な類似 { -track } が見つかりませんでした

# feeluown.gui.widgets
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.widgets.ai_chat
# ----------------------------------------
ai-chat-input-placeholder = アシスタントとおしゃべり
ai-chat-send-button = 送信

# feeluown.gui.widgets.cover_label
# ----------------------------------------
show-original-image = 原寸大を表示

# feeluown.gui.widgets.img_card_list
# ----------------------------------------
remove-action = 削除
remove-action-video = { remove-action } ビデオ
remove-action-playlist = { remove-action } { -track-list }
remove-action-musician = { remove-action } { -musician }
remove-action-album = { remove-action } { -album }

## releaseDate: [date, datetime] datetime when album was published
## trackCount: [int] amount of tracks in this album
album-release-date = { $trackCount ->
    [0] { DATETIME($releaseDate, year: "numeric", day: "numeric", month: "numeric") }
    *[other] { DATETIME($releaseDate, year: "numeric", day: "numeric", month: "numeric") } 曲
}

# feeluown.gui.widgets.labels
# ----------------------------------------
error-message-prefix = { -error }：
info-message-prefix = { -info }：

# feeluown.gui.widgets.selfpaint_btn
# ----------------------------------------
configuration-button = 設定
discovery = 発見
homepage = ホーム
calender = カレンダー
top-list = チャート
favorites = お気に入り
hot = 人気
emoji-expression = 絵文字

# feeluown.gui.widgets.songs
# ----------------------------------------
track-source = ソース
track-duration = 再生時間

# feeluown.gui.widgets.tabbar
# ----------------------------------------

## Albums containting this track
track-contributed-albums = 参加アルバム

# feeluown.gui.widgets.magicbox
# ----------------------------------------
search-box-placeholder = { -track }、アーティスト、{ -album }、ユーザーを検索
search-box-tooltip =
    文字を直接入力してフィルター、Enter で検索
    >>> プレフィックスで Python コードを実行
    “==> 失恋ソング | あいみょん” で直接 { -track } を再生
    “=== 雨の日に聴きたい曲” で AI と対話
    # プレフィックスで表をフィルタリング
    > プレフィックスで fuo コマンド実行（未実装、PR歓迎）
search-box-ai-chat-unavailable = AI チャット機能は利用できません
search-box-play-track = 再生を試みます：{ $song }
search-box-play-track-ill-formed = 入力形式は “{ -track } タイトル | アーティスト” にしてください

# feeluown.gui.widgets.settings
# ----------------------------------------
app-config = アプリ設定
save-config = 保存
search-providers = 検索ソース
ai-radio-prompt = AI ラジオ（プロンプト）
player = プレイヤー

# feeluown.gui.widgets.login
# ----------------------------------------
cookies-dialog-login-button  = ログイン
cookies-dialog-web-login-btn = FeelUOwn 内蔵ブラウザでログイン
cookies-dialog-chrome-btn    = Chrome から Cookie を読み込む
cookies-dialog-firefox-btn   = Firefox から Cookie を読み込む
cookies-dialog-edge-btn      = Edge から Cookie を読み込む

cookies-dialog-tutorial =
    FeelUOwn はサードパーティ音楽プラットフォームへのログイン方法を提供します。
    <span style='color:red'>いずれか一つを選択</span>してください。<br/><br/>
    もし普段使っているブラウザでログイン済みなら「Cookie 読み込み」を優先してください。
    それ以外は「{ cookies-dialog-web-login-btn }」を推奨（pyqt webengine が必要）。
    手動で Cookie をコピーできる場合は、先にコピーしてから「ログイン」をクリックしてください。

cookies-dialog-placeholder =
    ブラウザから Cookie をコピーしてください！

    Cookie Header をコピー（key1=value1; key2=value2 の形式）、
    または JSON 形式（{"{"}"key1": "value1", "key2": "value2"{"}"}）でも可。

cookies-parse-fail    = { $parser } パーサーでの解析に失敗、次を試します
cookies-parse-success = { $parser } パーサーでの解析に成功

cookies-save-user-info        = ユーザー情報を FeelUOwn データディレクトリに保存
cookies-loading-existing-user = 既存ユーザーを読み込み中…

# feeluown.gui.widgets.table_toolbar
# ----------------------------------------
play-all-button = すべて再生
play-all-button-fetching = すべての曲を取得中…
play-all-button-fetch-done = { play-all-button-fetching } 完了

album-filter-all = すべての { -album }
album-filter-standard = 標準
album-filter-singular-or-ep = シングル & EP
album-filter-live = ライブ
album-filter-compilation-retrospective = コンピレーション/ベスト

# feeluown.gui.widgets.meta
# ----------------------------------------

## dateTime: [date, datetime]
## https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat
meta-created-at =
    🕛 作成日時
    <code style="font-size: medium">
        { DATETIME($dateTime, year: "numeric", day: "numeric", month: "numeric") }
    </code>
meta-updated-at =
    🕛 更新日時
    <code style="font-size: medium">
        { DATETIME($dateTime, year: "numeric", day: "numeric", month: "numeric") }
    </code>
meta-released-at =
    🕛 リリース日時
    <code style="font-size: medium">
        { DATETIME($dateTime, year: "numeric", day: "numeric", month: "numeric") }
    </code>

## songsCount: [int] number of songs, -1 for unknown
meta-amount-songs = { $songsCount ->
    [-1] 不明
    [0] 曲なし
    *[other] <code style="font-size: medium">{ $songsCount }</code> 曲
}

# feeluown.gui.widgets.volume_button
# ----------------------------------------
volume-button-tooltip = 音量を調整

# feeluown.gui.widgets.playlists
# ----------------------------------------
track-list-remove = この { -track-list } を削除

# status: [string], 'succ' for success, 'fail' for failure
playlist-add-track = { -track } を { playlist } に追加{ $status ->
    [succ] 成功
   *[fail] 失敗
}

# feeluown.gui.widgets.provider
# ----------------------------------------
logged = ログイン済み

# feeluown.gui.widgets.progress_slider
# ----------------------------------------
drag-to-seek-progress = ドラッグしてシークを調整

# feeluown.gui.widgets.songs
# ----------------------------------------
add-to-playlist = プレイリストに追加
remove-from-playlist = { -track } を削除

# feeluown.gui.uimain
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.uimain.ai_chat
# ----------------------------------------
ai-chat-header = AI アシスタント
ai-chat-new = 新しい会話
ai-chat-match-resource = リソースをマッチング中…
ai-chat-match-resource-failed = マッチングに失敗
ai-chat-track-candidate-list = { -track } 候補リスト

# feeluown.gui.uimain.player_bar
# ----------------------------------------
album-released-at = アルバム発売日：{ $released }

# feeluown.gui.uimain.playlist_overlay
# ----------------------------------------
playlist-clear = { playlist } をクリア
jump-to-playing-track = 現在の { -track } へジャンプ

song-radio-mode = 自動追加
song-radio-mode-empty-playlist = プレイリストが空のため「{ song-radio-mode }」を有効化できません
song-radio-mode-activated = 「{ song-radio-mode }」を有効化しました

playback-mode = 再生モード
playback-mode-change = { playback-mode } を変更
playback-mode-single-repeat = 1曲リピート
## play songs in original order, on end stop playing
playback-mode-sequential = 順番再生
## play songs in original order, on end back to the first
playback-mode-loop = ループ再生
## play songs in random order
playback-mode-random = ランダム再生

# feeluown.gui.uimain.lyric
# ----------------------------------------
lyric-not-available = 利用可能な歌詞が見つかりません
lyric-background-color = 背景色
lyric-text-color = 文字色
lyric-font = フォント
lyric-show-bilingual = バイリンガル表示
lyric-window-auto-resize = 自動リサイズ

# feeluown.gui.uimain.nowplaying_overlay
# ----------------------------------------
similar-tracks = 類似 { -track }
track-hot-comments = ホットコメント
movie-mode-exit = ビデオモードを終了

# feeluown.gui.uimain.sidebar
# ----------------------------------------
-local-favorites = ローカルお気に入り
local-favorites = { -local-favorites }

collections-header-tooltip =
    ローカルで { -track-collection } を作成してお気に入りを管理できます

    各 { -track-collection } は .fuo ファイルとして存在し、マウスオーバーでパスを確認可能。
    新規 .fuo ファイルを作成すると新しい { -track-collection } が作成され、名前はファイル名になります。

    手動で .fuo を編集して { -track-collection } の内容を変更できますし、ドラッグ＆ドロップで { -track } を追加・削除できます。
ai-configure-tooltip =
    openai ライブラリをインストールし、以下を設定すれば AI アシスタントが使えます
    config.OPENAI_API_KEY = sk-xxx
    config.OPENAI_API_BASEURL = http://xxx
    config.OPENAI_API_MODEL = モデル名

collection-id = ID
collection-title = タイトル

## collectionName: [string] title/name of the collection
collection-already-exists = { -track-collection } ‘{ $collectionName }’ はすでに存在します
collection-confirm-remove = { -track-collection } ‘{ $collectionName }’ を削除してもよろしいですか？

# feeluown.gui.uimain.toolbar
# ----------------------------------------
-search-bar = 検索バー
search-bar-show = { -search-bar } を表示
search-bar-hide = { -search-bar } を閉じる

# feeluown.gui.uimain.provider_bar
# ----------------------------------------
my-favorite-button = { my-favorite-title }
my-playlists = { -track-list } リスト
my-tracks = マイミュージック
provider-unknown-tooltip = 現在の { -provider } は不明
fold-top-tooltip = { fold-collapse }/{ fold-expand } “ホーム と { -local-favorites }” 機能

## providerName: [string] name of the provider
provider-recommended-page-enter = { $providerName } のおすすめページに移動

provider-custom-ui-missing = 現在の { -provider } は UI が未登録です

## Note: this can also be due to missing of logged user
playlist-create-unsupported = 現在の { -provider } は { -track-list } 作成をサポートしていません
## providerName: [string] name of the provider
playlist-remove-unsupported = { -provider } の { $providerName } はプレイリスト削除をサポートしていません

## playlistTitle: [string]
## errorMessage: [string]
playlist-create-succed = { -track-list } ‘{ $playlistTitle }’ を作成しました
playlist-create-failed = { -track-list } ‘{ $playlistTitle }’ の作成に失敗: { $errorMessage }
playlist-remove-succed = { -track-list } ‘{ $playlistTitle }’ を削除しました
playlist-remove-failed = { -track-list } ‘{ $playlistTitle }’ の削除に失敗: { $errorMessage }

playlist-remove-confirm = プレイリスト ‘{ $playlistTitle }’ を削除してもよろしいですか？

playlist-name = { -track-list } 名

# feeluown.gui.pages.song_explore
# ----------------------------------------
track-lyrics = 歌詞
track-start-play = 再生
track-webpage-url-copy = ウェブページの URL をコピー
track-belongs-album = 所属 { -album }
release-date = 発売日
track-genre = ジャンル

## url: [string]
track-webpage-url-copied = コピーしました：{ $url }

## providerName: [string]
## This happens if user uninstalled a plugin, or modified
## their collections by hand, e.g.
track-source-provider-missing = 対応する { -provider } { $providerName } がありません

error-message-template =
    <p style="color: grey; font: small;">このプロバイダーはまだ{"{"}feature{"}"}に対応していません。
    <br/> { $interface } インターフェースを実装してサポートしましょう ~
    </p>
find-similar-tracks = { similar-tracks } を探す
track-view-comments = { -track } のコメントを見る

# feeluown.gui.pages
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.pages.coll_mixed
# ----------------------------------------
-music-library = 音楽ライブラリ
music-library = { -music-library }

music-library-empty = { -music-library } はまだ何もありません。追加しましょう！
collection-is-empty = この { -track-collection } はまだ何もありません。追加しましょう！

## item: [string]
remove-item-succeed = { $item } を削除しました

# feeluown.gui.pages.homepage
# ----------------------------------------
fold-expand = 展開
fold-collapse = 収縮
fold-tooltip = { fold-expand }/{ fold-collapse }

recommended-playlist = おすすめプレイリスト
recommended-daily-playlist = 今日のおすすめ
recommended-feelin-lucky = おまかせ再生
recommended-videos = ビデオを見る
recommended-videos-missing = おすすめ { video } はありません

# feeluown.gui.pages.my_dislike
# ----------------------------------------

## providerName: [string] name of the provider
## resType: [string] 'unknown', 'dislike'
provider-unsupported = 現在の { -provider }（{ $providerName }）は { $resType ->
    [dislike] 嫌いな { -track }
    *[unknown] 不明なリソースタイプ
} をサポートしていません

# feeluown.gui.pages.my_fav
# ----------------------------------------

## providerName: [string] name of the provider
## mediaType: [string] can be one of:
##    track
##    album
##    singer
##    playlist
##    video
provider-missing-favorite = 現在の { -provider }（{ $providerName }）はお気に入りの{ $mediaType ->
    [track] { -track }
    [album] { album }
    [singer] { musician }
    [playlist] { -track-list }
    [video] { video }
   *[other] コンテンツ
} を取得できません
provider-unknown-cannot-view = 現在の { -provider } は不明で、このページを表示できません
my-favorite-title = マイお気に入り

# feeluown.gui.pages.recommendation
# ----------------------------------------
music-blacklisted = ブラックリスト入り楽曲

## Similar to Spotify Radio
-music-radio-radar = ハートレーダー
music-radio-radar = { -music-radio-radar }
music-radio-radar-activated = { -music-radio-radar } を有効化しました
## Generate Radio stream based on the new track
music-radio-radar-changed = { -music-radio-radar } を切り替えました
## Find music recommendations
music-discovery = 音楽を発見
## デイリーおすすめプレイリスト
music-customized-recommendation = デイリーおすすめプレイリスト

# feeluown.gui.pages.provider_home
# ----------------------------------------
provider-liked-music = マイミュージック
provider-playlist-list = { -track-list } リスト

# feeluown.gui.pages.toplist
# ----------------------------------------
# ref: provider-unknown-cannot-view
# ref: top-list

# feeluown.gui.pages.model
# ----------------------------------------
provider-unsupported-fetch-artist-contributed-works =
    { -provider } は { -musician } の貢献アルバム取得をサポートしていません
provider-unsupported-fetch-artist-works =
    { -provider } は { -musician } のアルバム取得をサポートしていません
provider-unsupported-fetch-artist = { -provider } は { -musician } の曲取得をサポートしていません
provider-unsupported-fetch-album = { -provider } は { -album } の曲取得をサポートしていません
provider-unsupported-fetch-playlist = { -provider } は { -track-list } の曲取得をサポートしていません

## songTitle: [string]
track-playlist-remove-succ = { -track } “{ $songTitle }” を削除しました
track-playlist-remove-fail = { -track } “{ $songTitle }” の削除に失敗しました

# feeluown.gui.tray
# ----------------------------------------

## action: [string] "show", "hide"
## Show and focus app main window after hide to tray
tray-main-window-action = { $action ->
    [show] アクティブ化
   *[hide] 非表示
} メインウィンドウ

## action: [string] "play", "pause"
tray-toggle-playpause = { $action ->
    [pause] 一時停止
    *[play] 再生
}

tray-skip-track-next = 次の曲
tray-skip-track-prev = 前の曲

tray-quit-application = 終了

# feeluown.player
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.player.fm
# ----------------------------------------
track-radio-not-enough = ラジオの { -track } が不足しているため、FM モードを終了します

# feeluown.player.playlist
# ----------------------------------------
## errorMessage: [string]
track-url-fetch-failed = { -track } のリンク取得に失敗: { $errorMessage }

-music-video = ミュージックビデオ
track-fallback-music-video = { -music-video } を再生リソースとして使用 ✅
track-fallback-no-music-video = 利用可能な { -music-video } が見つかりません 🙁

music-video-not-avaliable = 利用可能な { -music-video } が見つかりません

playback-url-unavailable = 使用可能な再生リンクがありません

## standby: [string] standby provider for this resource
## track: the target track to play
track-standby-try = { $track } に利用可能な再生リソースがありません、代替の { -track } を探します…
track-standby-found = { $standby } で { $track } の代替 { -track } を見つけました ✅
track-standby-unavailable = { $track } の代替 { -track } が見つかりません

track-skip-to-next = 利用可能な再生リンクが見つからなかったため、次の曲を再生します…

# feeluown.gui.page_containers
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# feeluown.gui.page_containers.table
# ----------------------------------------

## errorMessage: [string]
provider-missing-feature = { -provider(capitalization: "uppercase") } はこの機能をサポートしていません: { $errorMessage }
provider-network-error = リクエストに失敗しました: { $errorMessage }
