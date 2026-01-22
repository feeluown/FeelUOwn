import os
import sys
import logging
from importlib import resources
from threading import RLock

import langcodes
from fluent.runtime import FluentLocalization, FluentResourceLoader

import feeluown.i18n

L10N_BUNDLE: FluentLocalization | None = None
_L10N_BUNDLE_LOCK = RLock()

# Comma separated list
OVERRIDE_LOCALE = os.environ.get("FEELUOWN_LOCALE", None)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def t(msg_id: str, **kwargs: object) -> str:
    """
    :param msg_id: Message ID inside fluent translation files.
    :param kwargs: Any object that implements the `__str__`
    """
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
            locales = [rfc1766_langcode()]
        else:
            locales = [OVERRIDE_LOCALE]

    logger.info(f"Loading locales for: {locales}")

    # Simple fallback,
    # en_US -> en, e.g.
    with _L10N_BUNDLE_LOCK:
        if L10N_BUNDLE is None:
            L10N_BUNDLE = load_l10n_resource(locales=locales)

    return L10N_BUNDLE


def load_l10n_resource(locales: list[str]) -> FluentLocalization:
    with resources.as_file(
        resources.files(feeluown.i18n) / "app",
    ) as current_dir:
        supported = [lang.removesuffix(".ftl") for lang in os.listdir(current_dir)]
        # The 'str' typing hint of `roots` is incorrect
        res_loader = FluentResourceLoader(roots=[current_dir])

        matched_locales = []
        for locale in locales:
            matched_best = langcodes.closest_supported_match(
                desired_language=locale,
                supported_languages=supported,
            )
            if matched_best is not None:
                matched_locales.append(matched_best)

        logger.info(f"matched locale: {matched_locales}")

        # resources are loaded immediately,
        # so current_dir can be cleaned safely.
        return FluentLocalization(
            # add en-US, zh-CN for fallback
            locales=matched_locales + ["en-US", "zh-CN"],
            resource_ids=["{locale}.ftl"],
            resource_loader=res_loader,
        )


if (
    sys.platform == "win32"
    and sys.version_info.major == 3
    and sys.version_info.minor >= 15
):
    from winrt.windows.system.userprofile import GlobalizationPreferences  # type: ignore


def rfc1766_langcode() -> str:
    """
    Returns a RFC 1766 language code, for current user preference.
    """

    import locale

    match sys.platform:
        case "win32" if sys.version_info.major == 3 and sys.version_info.minor >= 15:
            lang = GlobalizationPreferences.languages[0]
        case "win32":
            lang, _ = locale.getdefaultlocale()
        case _:
            lang, _ = locale.getlocale(locale.LC_CTYPE)
            if lang == "C":
                lang = "en-US"

    return lang


if __name__ == "__main__":
    l10n_en = l10n_bundle(locales=["en_US"])
    print(l10n_en.format_value("track"))
