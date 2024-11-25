from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING, runtime_checkable, Protocol, Dict, Optional, List, Callable, Any,
)

from PyQt5.QtCore import pyqtSignal, QObject

from feeluown.library import ProviderV2
from feeluown.gui.widgets.provider import ProvidersModel
from feeluown.utils.dispatch import Signal

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


@dataclass
class NavBtn:
    icon: str
    text: str
    cb: Callable[[], Any]


@runtime_checkable
class UISupportsLoginOrGoHome(Protocol):
    @abstractmethod
    def login_or_go_home(self):
        """This method is called when the avatar is clicked.

        Typically, ProviderUI can implement this method as follows:
        - When no user is logged in, ProviderUI MAY show a login dialog.
        - When a user is logged in, ProviderUI MAY show the homepage.
          At the same time, ProviderUI MAY emit a login success event.
        """


@runtime_checkable
class UISupportsLoginEvent(Protocol):
    """
    When the user is logged in, ProviderUI MAY emit a login success event.
    This allows FeelUOwn to perform certain actions based on this event,
    for example, fetching and show the user's playlist.
    """

    @property
    @abstractmethod
    def login_event(self):
        """
        event:
          0: first login failed
          1: first login ok
          2: re-login ok

        :return: Signal(provider_ui, event)
        """
        ...


@runtime_checkable
class UISupportsDiscovery(Protocol):

    @abstractmethod
    def discovery(self):
        ...


@runtime_checkable
class UISupportsNavBtns(Protocol):
    """
    Provider UI can add its own navigation buttons to the sidebar.
    """

    @abstractmethod
    def list_nav_btns(self) -> List[NavBtn]:
        ...


@runtime_checkable
class UISupportsCreatePlaylist(Protocol):
    """
    Provider UI can create playlist.
    """

    @abstractmethod
    def create_playlist(self):
        ...


class AbstractProviderUi(ABC):
    """Abstract base class for provider ui."""

    def get_colorful_svg(self) -> str:
        """Get provider's svg icon path."""
        return 'icons:feeluown.png'

    def register_pages(self, route):
        ...

    @property
    @abstractmethod
    def provider(self) -> ProviderV2:
        ...


class CurrentProviderUiManager(QObject):

    changed = pyqtSignal([object, object])

    def __init__(self, app: 'GuiApp'):
        super().__init__(parent=app)
        self._app = app
        self._current: Optional[AbstractProviderUi] = None

        # Old code uses `ProviderUiItem` to represent a provider.
        # New code should use `AbstractProviderUI` instead.
        self._current_item: Optional[ProviderUiItem] = None

    def get(self):
        return self._current

    def set(self, provider_ui: AbstractProviderUi):
        self._current_item = None
        old = self._current
        self._current = provider_ui
        self.changed.emit(provider_ui, old)

    def get_either(self):
        return self._current or self._current_item

    def get_item(self):
        return self._current_item

    def set_item(self, item: 'ProviderUiItem'):
        self._current = None
        self._current_item = item


class ProviderUiManager:
    """
    Note that `*_item` APIs are deprecated, new code should not use them anymore.
    """

    def __init__(self, app: 'GuiApp'):
        self._app = app

        self._store: Dict[str, AbstractProviderUi] = {}  # {name: provider_ui}

        self._items: Dict[str, ProviderUiItem] = {}  # name:model mapping
        self.model = ProvidersModel(self._app.library, self._app)

    def register(self, provider_ui: AbstractProviderUi):
        name = provider_ui.provider.meta.identifier
        if name in self._store or name in self._items:
            raise ValueError(f'provider_ui {name} already registered.')
        self._store[name] = provider_ui

        provider_ui.register_pages(self._app.browser.route)

    def get(self, identifier) -> Optional[AbstractProviderUi]:
        return self._store.get(identifier)

    def list_all(self) -> List[AbstractProviderUi]:
        return list(self._store.values())

    ####################################
    # The following are Deprecated APIs.
    ####################################
    def create_item(self, name, text, symbol='♬ ', desc='', colorful_svg=None):
        # pylint: disable=too-many-arguments
        provider = self._app.library.get(name)
        return ProviderUiItem(name,
                              text,
                              symbol,
                              desc,
                              colorful_svg=colorful_svg,
                              provider=provider)

    def get_item(self, name):
        return self._items.get(name)

    def list_items(self):
        return list(self._items.values())

    def add_item(self, uiitem):
        name = uiitem.name
        self.model.assoc(name, uiitem)
        self._items[name] = uiitem
        return True

    def remove_item(self, uiitem):
        if isinstance(uiitem, ProviderUiItem):
            name = uiitem.name
        else:
            name = uiitem
        if name in self._items:
            self.model.remove(name)
            self._items.pop(name)
            return True
        return False


class ProviderUiItem:
    """
    .. versiondeprecated:: 3.8.15
        Use `AbstractProviderUI` instead.
    """

    def __init__(self, name, text, symbol, desc, colorful_svg=None, provider=None):
        # pylint: disable=too-many-arguments
        # 如果需要，可以支持右键弹出菜单
        self._name = name
        self.text = text
        self.symbol = symbol
        self.desc = desc
        self.colorful_svg = colorful_svg
        self.provider = provider
        self.clicked = Signal()

    @property
    def name(self):
        return self._name
