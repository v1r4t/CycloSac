"""Glossary: fail-fast if glossary/{lang}.json missing (= exit 2)."""
import json
from pathlib import Path
from . import config


class GlossaryError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.code = config.EXIT_LOADER_FAIL


def load(inputs_dir: str, lang: str) -> dict:
    p = Path(inputs_dir) / "glossary" / f"{lang}.json"
    if not p.exists():
        raise GlossaryError(f"glossary missing: {p}")
    return json.loads(p.read_text())
