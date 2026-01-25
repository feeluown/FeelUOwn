import os
import sys
import logging
from decimal import Decimal
from datetime import date, datetime
from importlib import resources
from threading import RLock
from collections import defaultdict

import langcodes
from fluent.runtime import FluentLocalization, FluentResourceLoader

import feeluown.i18n

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


_L10N_BUNDLE: dict[tuple[str, ...], FluentLocalization] = {}
_L10N_BUNDLE_LOCK: dict[tuple[str, ...], RLock] = defaultdict(RLock)


def t(
    msg_id: str,
    locale: str = None,
    **kwargs: str | int | float | Decimal | date | datetime | object,
) -> str:
    """
    :param msg_id: Message ID inside fluent translation files.
    :param locale: Optional BCP-47 language code
    :param kwargs: Any object that implements the `__str__`

    If `locale` was left `None`, this will use the _DEFAULT_LOCALE.

    To format DATETIME() correctly, you must pass a date/datetime object.
    """
    if locale is None:
        locale = _DEFAULT_LOCALE

    for k, v in kwargs.items():
        # Special types
        if not isinstance(
            v,
            (
                str,
                float,
                int,
                date,
                datetime,
                Decimal,
            ),
        ):
            kwargs[k] = str(v)

    return l10n_bundle(locale).format_value(msg_id, kwargs)


def l10n_bundle(locale: str | None = None) -> FluentLocalization:
    """
    You could call this method multiple times

    **NOTE:** `locale.getlocale` from standard library is unreliable.

    :param locale: BCP-47 language code.
    :return: l10n localization bundle
    """
    if locale is None:
        if OVERRIDE_LOCALE is None:
            locale = rfc1766_langcode()
        else:
            locale = OVERRIDE_LOCALE

    return load_l10n_resource(locales=[locale])


def load_l10n_resource(locales: list[str]) -> FluentLocalization:
    with resources.as_file(
        resources.files(feeluown.i18n) / "assets",
    ) as current_dir:
        supported = [lang for lang in os.listdir(current_dir)]
        # The 'str' typing hint of `roots` is incorrect
        res_loader = FluentResourceLoader(roots=[current_dir / "{locale}"])

        matched_locales = []
        for locale in locales:
            matched_best = langcodes.closest_supported_match(
                desired_language=locale,
                supported_languages=supported,
            )
            if matched_best is not None:
                matched_locales.append(matched_best)

        locales_to_load = matched_locales + ["en-US", "zh-CN"]

        cache_key = tuple(locales_to_load)
        with _L10N_BUNDLE_LOCK[cache_key]:
            if cache_key in _L10N_BUNDLE:
                return _L10N_BUNDLE[cache_key]

            logger.info(f"Loading locale for: {locales_to_load}")

            # resources are loaded immediately,
            # so current_dir can be cleaned safely.
            bundle = FluentLocalization(
                # add en-US, zh-CN for fallback
                locales=locales_to_load,
                resource_ids=["app.ftl", "argparser.ftl"],
                resource_loader=res_loader,
            )

            _L10N_BUNDLE[cache_key] = bundle

        return bundle


def rfc1766_langcode() -> str:
    """
    Returns a RFC 1766 language code, for current user preference.
    """

    import locale

    match sys.platform:
        case "win32":
            from .windows import user_default_locale

            lang = user_default_locale()
        case _:
            lang, _ = locale.getlocale(locale.LC_CTYPE)
            if lang == "C":
                lang = "en_US"

    return lang


# BCP-47 language code
OVERRIDE_LOCALE = os.environ.get("FEELUOWN_LOCALE", None)
# Default locale
_DEFAULT_LOCALE = OVERRIDE_LOCALE if OVERRIDE_LOCALE is not None else rfc1766_langcode()


def human_readable_number(n: int, locale: str = None) -> str:
    """
    Compact number formatter

    :param n: the number
    :param locale: BCP-47 language code,
    """

    if locale is None:
        locale = _DEFAULT_LOCALE

    if locale.startswith("zh"):
        levels = [
            (100000000, "亿"),
            (10000, "万"),
        ]
    else:
        levels = [
            (1_000_000_000, "B"),
            (1_000_000, "M"),
            (1_000, "K"),
        ]

    for value, unit in levels:
        if n > value:
            first, second = n // value, (n % value) // (value // 10)
            return f"{first}.{second}{unit}"
    return str(n)


if __name__ == "__main__":
    l10n_en = l10n_bundle(locale="en_US")
    print(l10n_en.format_value("track"))
