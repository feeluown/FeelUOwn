# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QSizePolicy

from feeluown.libs.widgets.base import FFrame, FButton, FLabel, FScrollArea
from feeluown.libs.widgets.btns import _MultiSwitchButton
from feeluown.libs.widgets.labels import _BasicLabel
from feeluown.libs.widgets.sliders import _BasicSlider
from feeluown.libs.widgets.components import LP_GroupHeader, LP_GroupItem


class PlayerControlButton(FButton):
    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setObjectName('mc_btn')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                font-size: 13px;
                color: {1};
                outline: none;
            }}
            #{0}:hover {{
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color4.name())
        self.setStyleSheet(style_str)


class ProgressSlider(_BasicSlider):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)

        self.setOrientation(Qt.Horizontal)
        self.setMinimumWidth(400)
        self.setObjectName('player_progress_slider')


class VolumnSlider(_BasicSlider):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)

        self.setOrientation(Qt.Horizontal)
        self.setMinimumWidth(100)
        self.setObjectName('player_volumn_slider')


class ProgressLabel(_BasicLabel):
    def __init__(self, app, text=None, parent=None):
        super().__init__(app, text, parent)
        self._app = app

        self.setObjectName('player_progress_label')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
            }}
        '''.format(self.objectName(),
                   theme.color3.name())
        self.setStyleSheet(self._style_str + style_str)


class PlayerControlPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.previous_btn = PlayerControlButton(self._app, '上一首', self)
        self.pp_btn = PlayerControlButton(self._app, '播放', self)
        self.next_btn = PlayerControlButton(self._app, '下一首', self)
        self.progress_slider = ProgressSlider(self._app, self)
        self.volumn_slider = VolumnSlider(self._app, self)
        self.progress_label = ProgressLabel(self._app, '00:00/00:00', self)

        self._btn_container = FFrame(self)
        self._slider_container = FFrame(self)

        self._bc_layout = QHBoxLayout(self._btn_container)
        self._sc_layout = QHBoxLayout(self._slider_container)

        self.setObjectName('pc_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                color: {1};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._btn_container.setFixedWidth(140)
        self._slider_container.setMinimumWidth(700)

        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._bc_layout.setSpacing(0)
        self._bc_layout.setContentsMargins(0, 0, 0, 0)

        self._bc_layout.addWidget(self.previous_btn)
        self._bc_layout.addStretch(1)
        self._bc_layout.addWidget(self.pp_btn)
        self._bc_layout.addStretch(1)
        self._bc_layout.addWidget(self.next_btn)

        self._sc_layout.addWidget(self.progress_slider)
        self._sc_layout.addSpacing(2)
        self._sc_layout.addWidget(self.progress_label)
        self._sc_layout.addSpacing(5)
        self._sc_layout.addStretch(0)
        self._sc_layout.addWidget(self.volumn_slider)
        self._sc_layout.addStretch(1)

        self._layout.addWidget(self._btn_container)
        self._layout.addSpacing(10)
        self._layout.addWidget(self._slider_container)


class SongOperationPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.set_theme_style()

    def set_theme_style(self):
        pass


class TopPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.pc_panel = PlayerControlPanel(self._app, self)
        self.mo_panel = SongOperationPanel(self._app, self)

        self.setObjectName('top_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                color: {1};
                border-bottom: 1px solid {2};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.foreground_light.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setFixedHeight(50)
        self._layout.addSpacing(5)
        self._layout.addWidget(self.pc_panel)
        self._layout.addWidget(self.mo_panel)


class LP_LibraryPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.header = LP_GroupHeader(self._app, '我的音乐')
        self._layout = QVBoxLayout(self)

        self.setObjectName('lp_library_panel')
        self.set_theme_style()
        self.setup_ui()
        self.test()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.color3.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addSpacing(3)
        self._layout.addWidget(self.header)

    def test(self):
        for i in range(25):
            item = LP_GroupItem(self._app, '我喜欢的歌曲列表')
            self._layout.addWidget(item)
            if i in [2]:
                item.set_focus()


class LP_PlaylistsPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.header = LP_GroupHeader(self._app, '歌单')
        self._layout = QVBoxLayout(self)
        self.setObjectName('lp_playlists_panel')

        self.set_theme_style()
        self.setup_ui()
        self.test()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.header)

    def test(self):
        for i in range(5):
            item = LP_GroupItem(self._app, '国语经典-粤语')
            self._layout.addWidget(item)
            if i in [4]:
                item.set_focus()


class LeftPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.library_panel = LP_LibraryPanel(self._app)
        self.playlists_panel = LP_PlaylistsPanel(self._app)

        self._layout = QVBoxLayout(self)
        self.setObjectName('c_left_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.library_panel)
        self._layout.addWidget(self.playlists_panel)
        self._layout.addStretch(1)


class LeftPanel_Container(FScrollArea):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.left_panel = LeftPanel(self._app, self)
        self.setWidget(self.left_panel)

        self.ensureWidgetVisible(self.left_panel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setObjectName('c_left_panel_container')
        self.set_theme_style()
        self.setMinimumWidth(180)
        self.setMaximumWidth(220)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                border: 0px;
                border-right: 1px solid {1};
            }}
        '''.format(self.objectName(),
                   theme.foreground_light.name())
        self.setStyleSheet(style_str)


class RightPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app
        self._layout = QHBoxLayout(self)

        self.setup_ui()

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)


class RightPanel_Container(FScrollArea):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.right_panel = RightPanel(self._app)
        self._layout = QVBoxLayout(self)
        self.setWidget(self.right_panel)

        self.setObjectName('c_left_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                border: 0px;
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)


class CentralPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.left_panel_container = LeftPanel_Container(self._app, self)
        self.right_panel = RightPanel_Container(self._app, self)

        self._layout = QHBoxLayout(self)
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.left_panel_container)
        self._layout.addWidget(self.right_panel)


class SongLabel(FLabel):
    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setObjectName('song_label')
        self.setIndent(5)
        self.set_theme_style()

        self.set_song('Thank You - Dido / Dido')

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color7.name(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def set_song(self, song_text):
        self.setText('♪  ' + song_text + ' ')


class PlayerModeSwitchBtn(_MultiSwitchButton):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setObjectName('player_mode_switch_btn')
        self.set_theme_style()
        self.setText('♭ 随机')

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
                border: 0px;
                padding: 0px 4px;
            }}
        '''.format(self.objectName(),
                   theme.color6.name(),
                   theme.background.name())
        self.setStyleSheet(style_str)


class StatusPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.song_label = SongLabel(self._app, parent=self)
        self.pms_btn = PlayerModeSwitchBtn(self._app, self)

        self.setup_ui()
        self.setObjectName('status_panel')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
            }}
        '''.format(self.objectName(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setFixedHeight(18)
        # self.song_label.setMinimumWidth(220)
        self.song_label.setMaximumWidth(300)
        self._layout.addStretch(1)
        self._layout.addWidget(self.pms_btn)
        self._layout.addWidget(self.song_label)


class Ui(object):
    def __init__(self, app):
        self._layout = QVBoxLayout(app)
        self.top_panel = TopPanel(app, app)
        self.central_panel = CentralPanel(app, app)
        self.status_panel = StatusPanel(app, app)

        self.setup()

    def setup(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.top_panel)
        self._layout.addWidget(self.central_panel)
        self._layout.addWidget(self.status_panel)
