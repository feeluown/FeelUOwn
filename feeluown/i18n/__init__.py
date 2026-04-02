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


def load_l10n_resource(
    locales: list[str],
    skip_fallback: bool = False,
    resource_ids: list[str] = None,
) -> FluentLocalization:
    if resource_ids is None:
        resource_ids = DEFAULT_RESOURCE_IDS

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

        locales_to_load = matched_locales
        if not skip_fallback:
            locales_to_load += ["en-US", "zh-CN"]

        cache_key = (tuple(locales_to_load), tuple(resource_ids))
        with _L10N_BUNDLE_LOCK[cache_key]:
            if cache_key in _L10N_BUNDLE:
                return _L10N_BUNDLE[cache_key]

            logger.info(f"Loading locale for: {locales_to_load}")

            # resources are loaded immediately,
            # so current_dir can be cleaned safely.
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


# Plugin translation/localization
_plugin_locales = {}
_plugin_l10n_bundles = {}
_plugin_l10n_lock = RLock()


def register_plugin_locales(plugin_id: str, locales_dir: str | Path):
    """
    Registration for plugin locales dir
    """
    path = Path(locales_dir)
    if path.exists():
        _plugin_locales[plugin_id] = path
        logger.info(f"Registered i18n for plugin: {plugin_id}")


def _load_plugin_l10n_resource(plugin_id: str):
    if plugin_id not in _plugin_locales:
        return None

    with _plugin_l10n_lock:
        if plugin_id in _plugin_l10n_bundles:
            return _plugin_l10n_bundles[plugin_id]

        locales_dir = _plugin_locales[plugin_id]
        supported_locales = []

        if locales_dir.exists():
            supported_locales = [d.name for d in locales_dir.iterdir() if d.is_dir()]

        if not supported_locales:
            logger.warning(f"No locale directories found in {locales_dir}")
            return None

        use_locales = []
        for loc in supported_locales:
            if loc.replace("_", "-") == _DEFAULT_LOCALE:
                use_locales.append(loc)

        languages = ["zh-CN", "en-US", "ja-JP"]
        for langs in languages:
            if langs in supported_locales and langs not in use_locales:
                use_locales.append(langs)

        if not use_locales:
            use_locales.append(supported_locales[0])

        ftl_files = []
        first_dir = locales_dir / use_locales[0]
        for f in first_dir.glob("*.ftl"):
            ftl_files.append(f.name)

        loader = FluentResourceLoader(roots=[locales_dir/"{locale}"])
        bundle = FluentLocalization(locales=use_locales,
                                    resource_ids=ftl_files,
                                    resource_loader=loader)
        _plugin_l10n_bundles[plugin_id] = bundle
        logger.info(f"Loaded i18n for {plugin_id}, locales={use_locales}, files={ftl_files}")
        return bundle


if __name__ == "__main__":
    for res_id in DEFAULT_RESOURCE_IDS:
        resource_ids = [res_id]
        print(f"""{res_id}:
-----------------------------""")
        l10n_zh = next(
            load_l10n_resource(
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
                    load_l10n_resource(
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
