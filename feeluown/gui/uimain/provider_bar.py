from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QDialog,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
    QSizePolicy,
)

from feeluown.i18n import t
from feeluown.excs import ProviderIOError, NoUserLoggedIn
from feeluown.library import (
    SupportsPlaylistDelete,
    SupportsPlaylistCreateByName,
    SupportsCurrentUser,
)
from feeluown.utils import aio
from feeluown.gui.provider_ui import UISupportsNavBtns, UISupportsCreatePlaylist
from feeluown.gui.components import Avatar
from feeluown.gui.widgets import (
    DiscoveryButton,
    StarButton,
    PlusButton,
    TriagleButton,
    EmojiButton,
)
from feeluown.gui.widgets.playlists import PlaylistsView
from feeluown.gui.widgets.my_music import MyMusicView

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class ListViewContainer(QFrame):
    def __init__(self, label, view, parent=None):
        super().__init__(parent)

        self._btn_length = 14
        self._label = label
        self._view = view
        self._toggle_btn = TriagleButton(length=self._btn_length, padding=0.2)
        self.create_btn = PlusButton(length=self._btn_length)
        # Show this button when needed.
        self.create_btn.hide()

        self._toggle_btn.clicked.connect(self.toggle_view)
        self.setup_ui()

    def setup_ui(self):
        self._label.setFixedHeight(25)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._t_h_layout = QHBoxLayout()
        self._b_h_layout = QHBoxLayout()
        self._t_h_layout.addWidget(self._label)
        self._t_h_layout.addStretch(0)
        self._t_h_layout.addWidget(self.create_btn)
        self._t_h_layout.addSpacing(self._btn_length // 2)
        self._t_h_layout.addWidget(self._toggle_btn)
        self._b_h_layout.addWidget(self._view)

        self._layout.addLayout(self._t_h_layout)
        self._layout.addLayout(self._b_h_layout)
        # XXX: The original intent is to prevent any extra space from
        # appearing below the ListViewContainer.
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def toggle_view(self):
        if self._view.isVisible():
            self._toggle_btn.set_direction("down")
            self._view.hide()
        else:
            self._toggle_btn.set_direction("up")
            self._view.show()


LVC = ListViewContainer


class ProviderBar(QWidget):
    """
    A panel shows provider-specific contents.
    """

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent)
        self._app = app

        self.discovery_btn = DiscoveryButton(height=30, padding=0.2, parent=self)
        self.fav_btn = StarButton(t("my-favorite-button"), height=30, parent=self)
        self.fold_top_btn = TriagleButton(length=14, padding=0.2)
        self.fold_top_btn.setCheckable(True)

        self.playlists_header = QLabel(t("my-playlists"), self)
        self.my_music_header = QLabel(t("my-tracks"), self)

        self._layout = QVBoxLayout(self)
        # Layout to let provider add it's own buttons.
        self._btn_layout = QVBoxLayout()
        self.playlists_view = PlaylistsView(self)
        self.my_music_view = MyMusicView(self)
        self.playlists_view.setModel(self._app.pl_uimgr.model)
        self.my_music_view.setModel(self._app.mymusic_uimgr.model)

        self.playlists_con = LVC(self.playlists_header, self.playlists_view)
        self.my_music_con = LVC(self.my_music_header, self.my_music_view)

        self.playlists_view.show_playlist.connect(
            lambda pl: self._app.browser.goto(model=pl)
        )
        self.playlists_view.remove_playlist.connect(self._remove_playlist)
        self.playlists_con.create_btn.clicked.connect(self._create_playlist)
        self._app.current_pvd_ui_mgr.changed.connect(self.on_current_pvd_ui_changed)
        self.discovery_btn.clicked.connect(lambda: self._app.browser.goto(page="/rec"))
        self.fav_btn.clicked.connect(lambda: self._app.browser.goto(page="/my_fav"))

        self.setup_ui()

    def setup_ui(self):
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.playlists_view.setFrameShape(QFrame.Shape.NoFrame)
        self.my_music_view.setFrameShape(QFrame.Shape.NoFrame)

        self._avatar_layout = QHBoxLayout()
        self._avatar_layout.addWidget(Avatar(self._app, height=48))
        self._avatar_layout.addWidget(self.fold_top_btn)

        self._layout.addLayout(self._avatar_layout)
        self._layout.addWidget(self.discovery_btn)
        self._layout.addWidget(self.fav_btn)
        self._layout.addLayout(self._btn_layout)
        self._layout.addWidget(self.my_music_con)
        self._layout.addWidget(self.playlists_con)

        # Let each music library decide whether to display these components
        self.playlists_con.hide()
        self.my_music_con.hide()
        self.discovery_btn.setDisabled(True)
        self.fav_btn.setDisabled(True)
        self.discovery_btn.setToolTip(t("provider-unknown-tooltip"))
        self.fold_top_btn.setToolTip(t("fold-top-tooltip"))

    def on_current_pvd_ui_changed(self, pvd_ui, _):
        self._clear_btns()
        if pvd_ui:
            self.discovery_btn.setEnabled(True)
            self.fav_btn.setEnabled(True)
            self.discovery_btn.setToolTip(
                t("provider-recommended-page-enter", providerName=pvd_ui.provider.name)
            )
            if isinstance(pvd_ui, UISupportsNavBtns):
                for btn in pvd_ui.list_nav_btns():
                    qt_btn = EmojiButton(btn.icon, btn.text, height=30, parent=self)
                    qt_btn.clicked.connect(btn.cb)
                    self._add_btn(qt_btn)

            if isinstance(pvd_ui, UISupportsCreatePlaylist):
                self.playlists_con.create_btn.show()
                self.playlists_con.create_btn.clicked.connect(pvd_ui.create_playlist)
            else:
                self.playlists_con.create_btn.hide()
        else:
            self.discovery_btn.setEnabled(False)
            self.fav_btn.setEnabled(False)

    def _add_btn(self, btn):
        self._btn_layout.addWidget(btn)

    def _clear_btns(self):
        for _ in range(self._btn_layout.count()):
            item = self._btn_layout.takeAt(0)
            item.widget().deleteLater()
            del item

    def _create_playlist(self):
        provider_ui = self._app.current_pvd_ui_mgr.get()
        if provider_ui is None:
            self._app.show_msg(t("provider-custom-ui-missing"))
            return
        provider = provider_ui.provider
        if (
            not isinstance(provider, SupportsPlaylistCreateByName)
            or not isinstance(provider, SupportsCurrentUser)
            or not provider.has_current_user()
        ):
            self._app.show_msg(t("playlist-create-unsupported"))
            return

        dialog = QDialog(self)
        # Set WA_DeleteOnClose so that the dialog can be deleted (from self.children).
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        layout = QFormLayout(dialog)
        title_edit = QLineEdit(dialog)
        layout.addRow(t("playlist-name"), title_edit)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Yes
        )
        layout.addRow("", button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        def create_playlist_and_reload():
            title = title_edit.text()

            async def do():
                try:
                    playlist = await aio.run_fn(provider.playlist_create_by_name, title)
                except (ProviderIOError, NoUserLoggedIn) as e:
                    QMessageBox.warning(
                        self._app,
                        t("error"),
                        t(
                            "playlist-create-failed",
                            playlistTitle=title,
                            errorMessage=e,
                        ),
                    )
                else:
                    # Add playlist to pl_uimgr is a workaround, which may cause bug.
                    # For example, the order of the newly created playlist should be
                    # in the top for some providers.
                    # TODO: re-fetch user's playlists and fill the UI.
                    self._app.pl_uimgr.add(playlist, is_fav=False)
                    self._app.show_msg(t("playlist-create-succed", playlistTitle=title))

            aio.run_afn(do)

        dialog.accepted.connect(create_playlist_and_reload)
        dialog.open()

    def _remove_playlist(self, playlist):
        async def do():
            provider = self._app.library.get(playlist.source)
            if isinstance(provider, SupportsPlaylistDelete):
                ok = await aio.run_fn(provider.playlist_delete, playlist.identifier)
                self._app.show_msg(
                    t("playlist-create-succed", playlistTitle=playlist.name)
                    if ok
                    else t("playlist-create-failed", playlistTitle=playlist.name)
                )
                if ok is True:
                    self._app.pl_uimgr.model.remove(playlist)
            else:
                self._app.show_msg(
                    t("playlist-remove-unsupported", providerName=playlist.source)
                )

        box = QMessageBox(
            QMessageBox.Icon.Warning,
            t("info"),
            t("playlist-remove-confirm", playlistTitle=playlist.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            self,
        )
        box.accepted.connect(lambda: aio.run_afn(do))
        box.open()
