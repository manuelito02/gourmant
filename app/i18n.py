from pathlib import Path

from babel.support import NullTranslations, Translations
from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape

SUPPORTED_LANGS = ["en", "fr", "de", "nl"]
LANG_LABELS = {"en": "EN", "fr": "FR", "de": "DE", "nl": "NL"}

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_TRANSLATIONS_DIR = Path(__file__).parent.parent / "translations"

# Pre-build one Jinja2Templates instance and one Translations object per
# language at import time. Both are kept so gettext_for() doesn't re-read
# translation files from disk on every request.
_instances: dict[str, Jinja2Templates] = {}
_translations: dict[str, NullTranslations] = {}

for _lang in SUPPORTED_LANGS:
    _env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        extensions=["jinja2.ext.i18n"],
        autoescape=select_autoescape(["html"]),
    )
    _trans: NullTranslations
    if _lang == "en":
        _trans = NullTranslations()
    else:
        _trans = Translations.load(str(_TRANSLATIONS_DIR), [_lang])  # type: ignore[assignment]
    _env.install_gettext_translations(_trans)  # type: ignore[attr-defined]
    _instances[_lang] = Jinja2Templates(env=_env)
    _translations[_lang] = _trans

del _lang, _env, _trans  # clean up loop variables from module namespace


def get_lang(request: Request) -> str:
    lang = request.session.get("lang", "en")
    return lang if lang in SUPPORTED_LANGS else "en"


def get_templates(request: Request) -> Jinja2Templates:
    return _instances[get_lang(request)]


def gettext_for(request: Request, msgid: str) -> str:
    """Translate a string for the language stored in the current session."""
    return _translations[get_lang(request)].gettext(msgid)
