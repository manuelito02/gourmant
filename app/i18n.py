from pathlib import Path

from babel.support import NullTranslations, Translations
from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape

SUPPORTED_LANGS = ["en", "fr", "de", "nl"]
LANG_LABELS = {"en": "EN", "fr": "FR", "de": "DE", "nl": "NL"}

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_TRANSLATIONS_DIR = Path(__file__).parent.parent / "translations"

# Pre-build one Jinja2Templates instance per language at import time.
# Each has its own Jinja2 Environment with translations installed.
_instances: dict[str, Jinja2Templates] = {}

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

del _lang, _env, _trans  # clean up loop variables from module namespace


def get_lang(request: Request) -> str:
    lang = request.session.get("lang", "en")
    return lang if lang in SUPPORTED_LANGS else "en"


def get_templates(request: Request) -> Jinja2Templates:
    return _instances[get_lang(request)]


def gettext_for(request: Request, msgid: str) -> str:
    """Translate a string for the language stored in the current session."""
    lang = get_lang(request)
    if lang == "en":
        return msgid
    trans = Translations.load(str(_TRANSLATIONS_DIR), [lang])
    return trans.gettext(msgid)
