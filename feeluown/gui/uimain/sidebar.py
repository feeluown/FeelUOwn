import sys
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QScrollArea,
    QMessageBox,
    QFormLayout,
    QDialog,
    QLineEdit,
    QDialogButtonBox,
)

from feeluown.i18n import t
from feeluown.collection import CollectionAlreadyExists, CollectionType
from feeluown.utils.reader import create_reader, Reader
from feeluown.utils.aio import run_fn
from feeluown.gui.components import CollectionListView
from feeluown.gui.widgets import HomeButton, AIButton
from feeluown.gui.widgets.separator import Separator
from .provider_bar import ProviderBar, ListViewContainer as LVC

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class LeftPanel(QScrollArea):
    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent)
        self._app = app

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self.p = _LeftPanel(app, self)
        self.setWidget(self.p)

        if sys.platform.lower() != "darwin":
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # HELP(cosven): size policy is not working
        # self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        self.setMaximumWidth(280)

    def sizeHint(self):
        size = super().sizeHint()
        width = min(self._app.width() * 22 // 100, 240)
        return QSize(width, size.height())

    async def show_provider_current_user_playlists(self, provider):
        self.p.playlists_con.show()
        self._app.pl_uimgr.clear()

        playlists = await run_fn(provider.current_user_list_playlists)
        reader = await run_fn(provider.current_user_fav_create_playlists_rd)
        reader = create_reader(reader)
        assert isinstance(reader, Reader)
        fav_playlists = reader.readall()
        self._app.pl_uimgr.add(playlists)
        self._app.pl_uimgr.add(fav_playlists, is_fav=True)


class _LeftPanel(QFrame):
    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent)
        self._app = app

        self.home_btn = HomeButton(height=30, parent=self)
        self.ai_btn = AIButton(height=30, padding=0.2, parent=self)
        self.collections_header = QLabel(t("local-favorites"), self)
        self.collections_header.setToolTip(t("collections-header-tooltip"))
        self.collections_view = CollectionListView(self._app)
        self.collections_con = LVC(self.collections_header, self.collections_view)
        self._top_separator = Separator(self._app)
        self.provider_bar = ProviderBar(self._app)

        # For backward compatibility.
        self.playlists_con = self.provider_bar.playlists_con
        self.my_music_con = self.provider_bar.my_music_con
        self.playlists_header = self.provider_bar.playlists_header

        self._layout = QVBoxLayout(self)

        self._layout.setSpacing(0)
        self._layout.setContentsMargins(16, 10, 16, 0)
        self._layout.addWidget(self.home_btn)
        self._layout.addWidget(self.ai_btn)
        self._layout.addWidget(self.collections_con)
        self._layout.addWidget(self._top_separator)
        self._layout.addWidget(self.provider_bar)
        self._layout.addStretch(0)

        self.collections_view.show_collection.connect(
            lambda coll: self._app.browser.goto(page=f"/colls/{coll.identifier}")
        )
        self.collections_view.remove_collection.connect(self._remove_coll)
        self.collections_con.create_btn.clicked.connect(
            self.popup_collection_adding_dialog
        )
        self.collections_view.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.collections_con.create_btn.show()
        self.provider_bar.fold_top_btn.clicked.connect(self._toggle_top_layout)
        if self._app.config.ENABLE_NEW_HOMEPAGE is True:
            self.home_btn.clicked.connect(
                lambda: self._app.browser.goto(page="/homepage")
            )
        else:
            self.home_btn.clicked.connect(self.show_library)
        if self._app.ai is None:
            self.ai_btn.setDisabled(True)
            self.ai_btn.setToolTip(t("ai-configure-tooltip"))
        else:
            self.ai_btn.clicked.connect(self._app.ui.ai_chat_overlay.show)

    def _toggle_top_layout(self, checked):
        widgets = [
            self._top_separator,
            self.collections_con,
            self.home_btn,
            self.ai_btn,
        ]
        if checked:
            self.provider_bar.fold_top_btn.set_direction("down")
            for w in widgets:
                w.hide()
        else:
            self.provider_bar.fold_top_btn.set_direction("up")
            for w in widgets:
                w.show()

    def popup_collection_adding_dialog(self):
        dialog = QDialog(self)
        # Set WA_DeleteOnClose so that the dialog can be deleted (from self.children).
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        layout = QFormLayout(dialog)
        id_edit = QLineEdit(dialog)
        title_edit = QLineEdit(dialog)
        layout.addRow(t("collection-id"), id_edit)
        layout.addRow(t("collection-title"), title_edit)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save
        )
        layout.addRow("", button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        def create_collection_and_reload():
            fname = id_edit.text()
            title = title_edit.text()
            try:
                self._app.coll_mgr.create(fname, title)
            except CollectionAlreadyExists:
                QMessageBox.warning(
                    self,
                    t("warn"),
                    t("collection-already-exists", collectionName=fname),
                )
            else:
                self._app.coll_mgr.refresh()

        dialog.accepted.connect(create_collection_and_reload)
        dialog.open()

    def show_library(self):
        coll_library = self._app.coll_mgr.get_coll_library()
        self._app.browser.goto(page=f"/colls/{coll_library.identifier}")

    def show_pool(self):
        coll = self._app.coll_mgr.get(CollectionType.sys_pool)
        self._app.browser.goto(page=f"/colls/{coll.identifier}")

    def _remove_coll(self, coll):
        def do():
            self._app.coll_mgr.remove(coll)
            self._app.coll_mgr.refresh()

        box = QMessageBox(
            QMessageBox.Icon.Warning,
            t("info"),
            t("collection-confirm-remove", collectionName=coll.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            self,
        )
        box.accepted.connect(do)
        box.open()
