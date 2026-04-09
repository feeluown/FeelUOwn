import os
from pathlib import Path
import sys
import logging
from decimal import Decimal
from datetime import date, datetime
from importlib import resources
from threading import RLock
from collections import defaultdict

import langcodes
from fluent.runtime import FluentBundle, FluentLocalization, FluentResourceLoader

import feeluown.i18n

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


_L10N_BUNDLE: dict[tuple[str, ...], FluentLocalization] = {}
_L10N_BUNDLE_LOCK: dict[tuple[str, ...], RLock] = defaultdict(RLock)

_PLUGIN_LOCALES = {}


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
            if lang in ("C", None, ""):
                lang = "en_US"

    return lang


# BCP-47 language code
OVERRIDE_LOCALE = os.environ.get("FEELUOWN_LOCALE")
# Default locale
_DEFAULT_LOCALE = OVERRIDE_LOCALE or rfc1766_langcode() or "en_US"


def t(
    msg_id: str,
    locale: str = None,
    domain: str = None,
    **kwargs: str | int | float | Decimal | date | datetime | object,
) -> str:
    """
    :param msg_id: Message ID inside fluent translation files.
    :param locale: Optional BCP-47 language code
    :param domain: Plugin id, e.g. "fuo-netease".
                   If None, will go through l10n_bundle. (CORE)
                   If is passed, will go through plugin_l10n_bundle. (Plugin)
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

    if domain is None:
        bundle = l10n_bundle(locale)
    else:
        bundle = plugin_l10n_bundle(domain, locale)

    return bundle.format_value(msg_id, kwargs)


def register_plugin_i18n(domain: str, locales_dir: str | Path,
                         resource_ids: list[str]):
    """
    Registration for plugin i18n

    :param domain: Plugin id, e.g. "fuo-netease"
    :param locales_dir: Parent path of the locale files
    :param resource_ids: Locale file names as list
    """
    _PLUGIN_LOCALES[domain] = (Path(locales_dir), resource_ids)
    logger.info(f"Registered i18n for plugin: {domain}")


def l10n_bundle(locale: str | None = None) -> FluentLocalization:
    """
    Get bundle for CORE
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

    with resources.as_file(
            resources.files(feeluown.i18n) / "assets",
    ) as current_dir:
        supported = [lang for lang in os.listdir(current_dir)]
        roots = [str(current_dir / "{locale}")]

    return _create_or_get_bundle(namespace="CORE", roots=roots, locales=[locale],
                                 resource_ids=DEFAULT_RESOURCE_IDS, supported=supported)


def plugin_l10n_bundle(domain: str, locale: str | None = None) -> FluentLocalization:
    """
    Get bundle for plugin

    :param domain: Plugin id, e.g. "fuo-netease"
    :param locale: BCP-47 language code
    """
    if locale is None:
        if OVERRIDE_LOCALE is None:
            locale = rfc1766_langcode()
        else:
            locale = OVERRIDE_LOCALE

    if domain not in _PLUGIN_LOCALES:
        raise KeyError(f"Plugin not registered: {domain}")

    localedir, resource_ids = _PLUGIN_LOCALES[domain]
    supported = [d.name for d in localedir.iterdir() if d.is_dir()]
    roots = [localedir / "{locale}"]

    return _create_or_get_bundle(namespace=domain, roots=roots, locales=[locale],
                                 resource_ids=resource_ids, supported=supported)


def _create_or_get_bundle(
        namespace: str,
        roots: str | list[str],
        locales: list[str | None],
        resource_ids: list[str] = None,
        supported: list[str] = None,
        skip_fallback: bool = False
) -> FluentLocalization:
    """
    General logic for creating bundle

    :param namespace: "CORE" or Plugin domain id, e.g. "fuo-netease"
    """

    matched_locales = []
    for locale in locales:
        matched_best = langcodes.closest_supported_match(
            desired_language=locale,
            supported_languages=supported,
        )
        if matched_best is not None:
            matched_locales.append(matched_best)

    locales_to_load = matched_locales
    if not skip_fallback:
        locales_to_load += ["en-US", "zh-CN"]

    cache_key = (tuple(locales_to_load), tuple(resource_ids),
                 tuple(namespace))

    with _L10N_BUNDLE_LOCK[cache_key]:
        if cache_key in _L10N_BUNDLE:
            return _L10N_BUNDLE[cache_key]

        logger.info(f"Loading locale for: {locales_to_load}")

        # resources are loaded immediately,
        # so current_dir can be cleaned safely.
        res_loader = FluentResourceLoader(roots=roots)
        bundle = FluentLocalization(
            # add en-US, zh-CN for fallback
            locales=locales_to_load,
            resource_ids=resource_ids,
            resource_loader=res_loader,
        )

        _L10N_BUNDLE[cache_key] = bundle

    return bundle


def human_readable_number(n: int, locale: str = None) -> str:
    """
    Compact number formatter

    :param n: the number
    :param locale: BCP-47 language code,
    """

    locale = locale or _DEFAULT_LOCALE

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


DEFAULT_RESOURCE_IDS = ["app.ftl", "argparser.ftl", "config.ftl"]


if __name__ == "__main__":
    with resources.as_file(
            resources.files(feeluown.i18n) / "assets",
    ) as current_dir:
        supported = [lang for lang in os.listdir(current_dir)]
        roots = [str(current_dir / "{locale}")]

        for res_id in DEFAULT_RESOURCE_IDS:
            resource_ids = [res_id]
            print(f"""{res_id}:
    -----------------------------""")
            l10n_zh = next(
                _create_or_get_bundle(
                    namespace="CORE",
                    roots=roots,
                    locales=["zh-CN"],
                    skip_fallback=True,
                    resource_ids=resource_ids,
                )._bundles()
            )
            total_term_len = len(l10n_zh._terms)
            total_msg_len = len(l10n_zh._messages)
            for locale in os.listdir(Path(__file__).parent / "assets"):
                if locale == "zh-CN":
                    continue

                try:
                    bundle: FluentBundle = next(
                        _create_or_get_bundle(
                            namespace="CORE",
                            roots=roots,
                            locales=[locale],
                            skip_fallback=True,
                            resource_ids=resource_ids,
                        )._bundles()
                    )
                except StopIteration:
                    continue
                print(f"{locale}")

                if total_term_len:
                    print(
                        f"Terms: {len(bundle._terms)}/{total_term_len}"
                        f" ({100 * len(bundle._terms) / total_term_len:.1f}%)"
                    )
                if total_msg_len:
                    print(
                        f"Messages: {len(bundle._messages)}/{total_msg_len}"
                        f" ({100 * len(bundle._messages) / total_msg_len:.1f}%)"
                    )

                print()
