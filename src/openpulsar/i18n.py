from PySide6.QtCore import QLocale
from pathlib import Path
import json
import os


def _settings_language():
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "OpenPulsar"
    config_file = config_dir / "settings.json"

    try:
        payload = json.loads(config_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "system"

    language = payload.get("language", "system")
    if language in {"fr", "en", "de", "es"}:
        return language
    return "system"


def _system_language():
    system = QLocale.system().name().lower()

    if system.startswith("fr"):
        return "fr"
    if system.startswith("de"):
        return "de"
    if system.startswith("es"):
        return "es"
    return "en"


def _resolve_language(language=None):
    if language is None:
        language = _settings_language()

    if language == "system":
        return _system_language()

    if language in {"fr", "en", "de", "es"}:
        return language

    return "en"


def _load(lang):
    path = Path(__file__).parent / "translations" / f"{lang}.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


LANG = _resolve_language()
_TRANSLATIONS = _load(LANG)


def set_language(language):
    global LANG, _TRANSLATIONS
    LANG = _resolve_language(language)
    _TRANSLATIONS = _load(LANG)


def tr(text):
    return _TRANSLATIONS.get(text, text)
