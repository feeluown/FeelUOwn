import os
import sys
import locale
import logging
from importlib import resources
from threading import RLock

from babel import Locale
from fluent.runtime import FluentLocalization, FluentResourceLoader

import feeluown.i18n

L10N_BUNDLE: FluentLocalization | None = None
_L10N_BUNDLE_LOCK = RLock()

# Comma separated list
OVERRIDE_LOCALE = os.environ.get("FEELUOWN_LOCALE", None)

__all__ = ["t"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def t(msg_id: str, **kwargs: object) -> str:
    for k, v in kwargs.items():
        if not isinstance(v, (str, float, int)):
            kwargs[k] = str(v)

    return l10n_bundle().format_value(msg_id, kwargs)


def l10n_bundle(locales: list[str] | None = None) -> FluentLocalization:
    """
    You could call this method multiple times

    **NOTE:** `locale.getlocale` from standard library is unreliable.

    :param locales: RFC 1766 langcode list.
    :return: l10n localization bundle
    """
    global L10N_BUNDLE

    if locales is None:
        if OVERRIDE_LOCALE is None:
            locales = [babel_langcode()]
        else:
            locales = [OVERRIDE_LOCALE]

    logger.info(f"Loading locales for: {locales}")

    # Simple fallback,
    # en_US -> en, e.g.
    locales_with_fallback = []
    for locale_str in locales:
        if locale_str == "C":
            locale_str = "en_US"
        locales_with_fallback.append(locale_str)
        lang = Locale.parse(locale_str).language

        if lang != locale_str and lang not in locales_with_fallback:
            locales_with_fallback.append(lang)

    with _L10N_BUNDLE_LOCK:
        if L10N_BUNDLE is None:
            L10N_BUNDLE = load_l10n_resource(locales=locales_with_fallback)

    return L10N_BUNDLE


def load_l10n_resource(locales: list[str]) -> FluentLocalization:
    with resources.as_file(
        resources.files(feeluown.i18n),
    ) as current_dir:
        # The 'str' typing hint of `roots` is incorrect
        res_loader = FluentResourceLoader(roots=[current_dir / "{locale}"])

        # resources are loaded immediately,
        # so current_dir can be cleaned safely.
        return FluentLocalization(
            # add zh_CN for fallback
            locales=locales + ["zh_CN"],
            resource_ids=["app.ftl"],
            resource_loader=res_loader,
        )


def babel_langcode() -> str:
    if sys.version_info.major > 3 or sys.version_info.minor >= 15:
        raise NotImplementedError(
            "python locale.getlocale violates RFC 1766 on Windows"
        )
        # FIXME: need ICU for python >= 3.15
        lang, _encoding = locale.getlocale(locale.LC_CTYPE)
    else:
        lang, _encoding = locale.getdefaultlocale()
    return lang


if __name__ == "__main__":
    l10n_en = l10n_bundle(locales=["en_US"])
    print(l10n_en.format_value("track"))
