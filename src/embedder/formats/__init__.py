from __future__ import annotations

from pathlib import Path

from embedder.formats.base import Format
from embedder.formats.markdown import MarkdownFormat
from embedder.formats.text import TextFormat
from embedder.formats.yaml import YamlFormat

_SPECIFIC_FORMATS: list[Format] = [
    MarkdownFormat(),
    YamlFormat(),
]
_FALLBACK: Format = TextFormat()


def get_format(path: Path) -> Format:
    for fmt in _SPECIFIC_FORMATS:
        if fmt.matches(path):
            return fmt
    return _FALLBACK
