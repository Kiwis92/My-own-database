"""
i18n-laag conform de project brief: meertalig vanaf dag één.

- Vertalingen staan in app/locales/<taal>.json (nl, en, fr, de, es).
- NL is de bronttaal en altijd volledig; ontbrekende sleutels in andere talen
  vallen terug op Engels en daarna op Nederlands.
- Taalkeuze: ?lang= query-parameter > 'lang'-cookie > Accept-Language header > nl.
"""
import json
import os
from functools import lru_cache
from fastapi import Request

SUPPORTED = ["nl", "en", "fr", "de", "es"]
DEFAULT = "nl"
LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")


@lru_cache(maxsize=None)
def _load(locale: str) -> dict:
    path = os.path.join(LOCALES_DIR, f"{locale}.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_locale(request: Request) -> str:
    lang = request.query_params.get("lang")
    if lang in SUPPORTED:
        return lang
    lang = request.cookies.get("lang")
    if lang in SUPPORTED:
        return lang
    accept = request.headers.get("accept-language", "")
    for part in accept.split(","):
        code = part.split(";")[0].strip().lower()[:2]
        if code in SUPPORTED:
            return code
    return DEFAULT


def translate(locale: str, key: str, **kwargs) -> str:
    """Vertaal een sleutel; fallback-keten: locale -> en -> nl -> de sleutel zelf."""
    for lang in (locale, "en", "nl"):
        value = _load(lang).get(key)
        if value is not None:
            return value.format(**kwargs) if kwargs else value
    return key
