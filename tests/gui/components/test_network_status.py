import pytest
from PyQt6.QtCore import Qt

from feeluown.gui.drawers import ProxyIconDrawer, ProxyShieldBadgeDrawer
from feeluown.gui.components.network_status import (
    NetworkStatusButton,
    sanitize_proxy_url,
    sanitize_proxies,
    format_proxies_for_display,
)
from feeluown.i18n import t


def test_network_status_button_updates_sanitized_tooltip(qtbot, app_mock):
    btn = NetworkStatusButton()
    qtbot.addWidget(btn)

    btn.update_proxy_status(
        {
            "http": "http://user:pass@127.0.0.1:7890",
            "https": "socks5://127.0.0.1:7891",
        }
    )

    assert btn.toolTip() == t(
        "proxy-detected",
        proxyInfo="http=http://127.0.0.1:7890\nhttps=socks5://127.0.0.1:7891",
    ) + "\n\n" + t("proxy-click-to-refresh")
    assert btn._has_proxy is True


def test_network_status_button_click_refreshes_detected_proxy(
    qtbot, app_mock, monkeypatch
):
    proxies = [
        {},
        {
            "http": "http://user:pass@127.0.0.1:7890",
            "https": "socks5://127.0.0.1:7891",
        },
    ]

    monkeypatch.setattr(
        "feeluown.gui.components.network_status.detect_proxy",
        lambda: proxies.pop(0),
    )

    btn = NetworkStatusButton()
    qtbot.addWidget(btn)
    qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)

    assert btn.toolTip() == t(
        "proxy-detected",
        proxyInfo="http=http://127.0.0.1:7890\nhttps=socks5://127.0.0.1:7891",
    ) + "\n\n" + t("proxy-click-to-refresh")
    assert btn._has_proxy is True


def test_network_status_button_shows_no_proxy_tooltip(qtbot, app_mock):
    btn = NetworkStatusButton()
    qtbot.addWidget(btn)

    btn.update_proxy_status({})

    assert btn.toolTip() == t("proxy-not-detected") + "\n\n" + t(
        "proxy-click-to-refresh"
    )
    assert btn._has_proxy is False


def test_network_status_button_detects_proxy_on_init(qtbot, app_mock, monkeypatch):
    monkeypatch.setattr(
        "feeluown.gui.components.network_status.detect_proxy",
        lambda: {
            "http": "http://user:pass@127.0.0.1:7890",
            "https": "socks5://127.0.0.1:7891",
        },
    )

    btn = NetworkStatusButton()
    qtbot.addWidget(btn)

    assert btn.toolTip() == t(
        "proxy-detected",
        proxyInfo="http=http://127.0.0.1:7890\nhttps=socks5://127.0.0.1:7891",
    ) + "\n\n" + t("proxy-click-to-refresh")
    assert btn._has_proxy is True


def test_network_status_button_has_fixed_square_width(qtbot, app_mock):
    btn = NetworkStatusButton(length=30)
    qtbot.addWidget(btn)

    assert btn.width() == 30
    assert btn.height() == 30
    assert btn._badge_drawer is not None


def test_proxy_icon_drawer_latitude_lines_end_on_globe_boundary():
    drawer = ProxyIconDrawer(length=30, padding=7)
    center = drawer._globe_rect.center()
    radius = drawer._globe_rect.width() / 2

    for line in (drawer._equator, drawer._north_latitude, drawer._south_latitude):
        left, right = line
        assert left.y() == pytest.approx(right.y())

        for point in (left, right):
            dx = point.x() - center.x()
            dy = point.y() - center.y()
            assert dx * dx + dy * dy == pytest.approx(radius * radius, abs=0.1)


def test_proxy_shield_badge_drawer_is_positioned_relative_to_icon_body():
    drawer = ProxyShieldBadgeDrawer(length=30, padding=6)

    assert drawer._bounding_rect.width() == pytest.approx(30 / 3.6)
    assert drawer._bounding_rect.height() == pytest.approx(30 / 3.6)
    assert drawer._bounding_rect.right() == pytest.approx(30 - 6 + 6 * 0.25)
    assert drawer._bounding_rect.bottom() == pytest.approx(30 - 6 + 6 * 0.25)
    assert drawer._polygon.count() == 6

    top = drawer._polygon.at(0)
    top_right = drawer._polygon.at(1)
    right_mid = drawer._polygon.at(2)
    bottom = drawer._polygon.at(3)
    left_mid = drawer._polygon.at(4)
    top_left = drawer._polygon.at(5)

    assert top.x() == pytest.approx(drawer._bounding_rect.center().x())
    assert bottom.x() == pytest.approx(drawer._bounding_rect.center().x())
    assert top_right.x() > right_mid.x()
    assert top_left.x() < left_mid.x()
    assert right_mid.y() > top_right.y()
    assert left_mid.y() > top_left.y()


def test_sanitize_proxy_url_removes_userinfo():
    assert (
        sanitize_proxy_url("http://user:pass@127.0.0.1:7890")
        == "http://127.0.0.1:7890"
    )


def test_sanitize_proxies_keeps_mapping_shape():
    proxies = {
        "http": "http://user:pass@127.0.0.1:7890",
        "https": "socks5://127.0.0.1:7891",
    }

    assert sanitize_proxies(proxies) == {
        "http": "http://127.0.0.1:7890",
        "https": "socks5://127.0.0.1:7891",
    }


def test_sanitize_proxy_url_keeps_ipv6_host_brackets():
    assert (
        sanitize_proxy_url("http://user:pass@[::1]:7890")
        == "http://[::1]:7890"
    )


def test_format_proxies_for_display_uses_sanitized_values():
    proxies = {"http": "http://user:pass@127.0.0.1:7890"}

    assert format_proxies_for_display(proxies) == "http=http://127.0.0.1:7890"
