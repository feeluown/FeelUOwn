# Dynamic Island Status Bar — 实现文档

## 背景

AI 聊天输入框底部原本有一个 `_msg_label`，用于显示类似
"AI Radio is active" 的静态提示。这个位置更适合承载当前播放状态：
用户视线集中在输入框时，可以直接看到“现在正在播什么”，也可以在
暂停或 hover 时完成上一首、播放/暂停、下一首操作。

因此，AI 聊天页新增 `DynamicIslandStatusBar`，作为
`ChatInputWidget` footer 左侧的可替换状态组件。它不属于顶部 toolbar。

## 设计决策

### 状态行为

| 状态 | 触发条件 | 显示内容 | 尺寸 |
|------|---------|---------|------|
| 紧凑态 (Compact) | 播放中 + 无 hover | 封面(20x20) + 居中的当前歌词行 | 高36px，宽随歌词动态变化(96-280px) |
| 展开态 (Expanded) | 暂停 / 播放中 hover | 封面(24x24) + LineSongLabel + prev/play/next/volume 按钮(22px) | 高36px，宽280px |
| 隐藏 | player.state == stopped | 不显示 | — |

### 组件结构

```
DynamicIslandStatusBar(QWidget)
├── QHBoxLayout
│   ├── CoverLabelV2 — 封面圆角3px，异步加载
│   ├── QLabel (lyric_label) — 歌词行，elided_text 省略
│   ├── LineSongLabel (song_label) — "标题 • 歌手" 单行，复用现有组件
│   └── QWidget (control_widget)
│       ├── PlayPreviousButton(length=22)
│       ├── PlayPauseButton(length=22, draw_circle=False)
│       ├── PlayNextButton(length=22)
│       └── VolumeButton(length=22)
```

### 动画方案

- **驱动**: QTimer @ 16ms (~60fps)，与项目已有 `AnimatedCoverLabel` 模式一致，不使用 QPropertyAnimation
- **步长**: 12px/tick (~750px/s)
- **逻辑**: 跟踪 `_anim_from`(起始宽度)、`_anim_to`(目标宽度)、`_anim_current`(当前宽度)
- **内容切换**: 动画进度达到 60% 时切换 compact/expanded 内容可见性。组件外部高度固定为 36px，hover 只改变宽度和内容，不改变输入框高度。

### 颜色

遵循 `docs/source/dev_best_practice.rst`：所有颜色来自 `QPalette`。
pill 背景在绘制时读取当前 `QGuiApplication.palette().Base` 并设置
alpha，避免组件自己私有感知系统主题变化。

### 播放控制

- 组件可聚焦；焦点在组件上时，左右方向键快退/快进 5 秒。
- 上下方向键降低/提高 10 音量。
- 展开态控制按钮组包含上一首、播放/暂停、下一首和音量按钮。
- `paintEvent` 使用当前播放进度在胶囊边框上绘制一段进度线。

## 涉及文件

### 新建: `feeluown/gui/uimain/dynamic_island_bar.py`

核心类 `DynamicIslandStatusBar(QWidget)`，约 230 行。

关键方法：

| 方法 | 职责 |
|------|------|
| `_setup_ui()` | 创建所有子组件和布局（遵循项目规范：UI 初始化放此方法） |
| `_connect_signals()` | 连接 player 信号（metadata_changed/state_changed）和 live_lyric.line_changed |
| `_on_metadata_changed(metadata)` | 加载封面(异步 via run_afn)、控制可见性 |
| `_on_player_state_changed(state)` | stopped→隐藏, paused→展开, playing→紧凑(无 hover) |
| `_on_lyric_line_changed(line)` | 更新歌词行文本，重算紧凑宽度 |
| `enterEvent/leaveEvent` | hover 展开/收拢 |
| `keyPressEvent` | 处理方向键快进/快退/音量调节 |
| `paintEvent` | 绘制胶囊形半透明背景和边框播放进度 |
| `_start_expand/_start_compact` | 启动动画 |
| `_tick_animation` | 动画每帧，更新 setFixedWidth |
| `_switch_to_expanded/_switch_to_compact` | 切换内容可见性和尺寸 |
| `_finalize_state` | 动画结束收尾 |
| `_calc_compact_width` | 根据歌词文本计算紧凑态自然宽度 |

使用的可复用组件：

| 组件 | 来源文件 |
|------|---------|
| `CoverLabelV2` | `feeluown/gui/widgets/cover_label.py` |
| `LineSongLabel` | `feeluown/gui/components/line_song.py` |
| `PlayPauseButton`, `PlayNextButton`, `PlayPreviousButton` | `feeluown/gui/widgets/selfpaint_btn.py` |
| `VolumeButton` | `feeluown/gui/widgets/volume_button.py` |
| `LiveLyric.line_changed` / `Line` 命名元组 | `feeluown/player/lyric.py` |
| `State` 枚举 | `feeluown/player/base_player.py` |

### 修改: `feeluown/gui/widgets/ai_chat.py`

`ChatInputWidget` 支持接收可选的 `status_widget`：

1. 有 `status_widget` 时，footer 左侧展示该组件，发送按钮仍在右侧。
2. `_msg_label` 保留为 fallback，供没有传入状态组件的旧用法继续使用。
3. `set_msg` 仍会更新 `_msg_label`，但在有 `status_widget` 时不显示它。

### 修改: `feeluown/gui/uimain/ai_chat.py`

在 `AIChatBox` 中创建 `DynamicIslandStatusBar(app)`，并传给
`ChatInputWidget(status_widget=...)`。顶部 `Body` toolbar 只保留标题和
三个操作按钮，不承载播放状态组件。

`_refresh_context` 只切换输入框 placeholder；AI Radio 的候选信息仍通过
playlist/sidebar 展示，不再占用输入框底部状态栏。

### 修改: `tests/gui/uimain/test_uimain.py`

1. 断言 `DynamicIslandStatusBar` 的 parent 是 `ChatInputWidget`。
2. 断言 toolbar layout 不包含该组件，避免后续回归到顶部。
3. 断言有 `status_widget` 时 `_msg_label` 隐藏。
4. 补充 mock：在 `test_ai_chat_overlay_reapplies_titlebar_mode_on_resize`
   中为 QWidget fake app 添加 `player.metadata_changed/state_changed/state`
   和 `live_lyric.line_changed`。

## 已知限制 / 待完善

1. **`line_changed` 信号直接连接**: 未用 `aioqueue=True`，原因是 `_on_lyric_line_changed` 需要同步更新 elided_text 并立即重算宽度。实际运行时该信号频率约 300ms 一次（由 `PlayerPositionDelegate` 驱动），不会阻塞主线程。

2. **LineSongLabel 内部连接**: `LineSongLabel` 构造函数内部连接了 `player.metadata_changed`（带 aioqueue）。该连接在 DynamicIsland 创建时建立，在 compact 态时 LineSongLabel 虽隐藏但仍会接收信号更新内部文本。这一行为是符合预期的——展开时文本始终是最新的。

3. **歌词文本 elide**: 紧凑态歌词使用 `elided_text()` 静态省略，当 pill 宽度因动画变化时不会实时重新 elide。但由于动画时 lyric_label 的可见性在 60% 进度就已切换，实际不可见，因此无影响。

4. **无切歌过渡动画**: 歌曲切换时封面和歌词直接刷新，无渐隐渐显效果。

5. **LineSongLabel 的 marquee**: 当鼠标从外部移入 pill → pill 展开 → LineSongLabel 直接出现在鼠标下方时，LineSongLabel 会收到 enterEvent 启动滚动。这是可接受的行为。

## 测试状态

已执行：

- `uv run flake8 feeluown/gui/uimain/ai_chat.py feeluown/gui/uimain/dynamic_island_bar.py feeluown/gui/widgets/ai_chat.py tests/gui/uimain/test_uimain.py` — passed
- `uv run pytest tests/gui/uimain/test_uimain.py -q` — 44 passed

## 后续可做

- 添加 `DynamicIslandStatusBar` 自身的单元测试
- 考虑允许用户点击 pill 跳转到 nowplaying 页面
