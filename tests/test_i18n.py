import locale

from feeluown import i18n


def test_rfc1766_langcode_fallback_for_missing_language(monkeypatch):
    monkeypatch.setattr(i18n.sys, "platform", "linux")
    monkeypatch.setattr(locale, "getlocale", lambda category=None: (None, "UTF-8"))

    assert i18n.rfc1766_langcode() == "en_US"


def test_human_readable_number_fallback_for_empty_locale_arg(monkeypatch):
    monkeypatch.setattr(i18n, "_DEFAULT_LOCALE", "en_US")

    assert i18n.human_readable_number(1_500, locale="") == "1.5K"


def test_human_readable_number_zh_locale():
    assert i18n.human_readable_number(12_000, locale="zh_CN") == "1.2万"
