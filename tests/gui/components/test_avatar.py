from types import SimpleNamespace
from unittest.mock import MagicMock

from feeluown.gui.components.avatar import Avatar


class DummyProvider:
    def __init__(self, identifier="dummy"):
        self.identifier = identifier
        self.current_user_changed = SimpleNamespace(connect=MagicMock())


def test_on_provider_added_connects_with_aioqueue(qtbot, app_mock):
    avatar = Avatar(app_mock)
    qtbot.addWidget(avatar)

    provider = DummyProvider()
    avatar.on_provider_added(provider)

    assert provider.current_user_changed.connect.call_count == 1
    _, kwargs = provider.current_user_changed.connect.call_args
    assert kwargs["weak"] is False
    assert kwargs["aioqueue"] is True


def test_current_user_changed_refreshes_when_provider_is_current(
    qtbot, app_mock, monkeypatch
):
    avatar = Avatar(app_mock)
    qtbot.addWidget(avatar)

    provider = DummyProvider()
    app_mock.current_pvd_ui_mgr.get.return_value = SimpleNamespace(provider=provider)

    run_afn_mock = MagicMock()
    monkeypatch.setattr("feeluown.gui.components.avatar.run_afn", run_afn_mock)

    user = SimpleNamespace(name="tester")
    cb = avatar.create_provider_current_user_changed_cb(provider)
    cb(user)

    assert avatar._logging_state[provider.identifier] == "tester"
    run_afn_mock.assert_any_call(avatar.show_pvd_ui_current_user)
    run_afn_mock.assert_any_call(
        app_mock.ui.sidebar.show_provider_current_user_playlists,
        provider,
    )


def test_current_user_changed_skip_refresh_when_provider_not_current(
    qtbot, app_mock, monkeypatch
):
    avatar = Avatar(app_mock)
    qtbot.addWidget(avatar)

    provider = DummyProvider("dummy")
    other_provider = DummyProvider("other")
    app_mock.current_pvd_ui_mgr.get.return_value = SimpleNamespace(
        provider=other_provider
    )

    run_afn_mock = MagicMock()
    monkeypatch.setattr("feeluown.gui.components.avatar.run_afn", run_afn_mock)

    cb = avatar.create_provider_current_user_changed_cb(provider)
    cb(SimpleNamespace(name="tester"))

    run_afn_mock.assert_not_called()
