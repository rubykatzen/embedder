from __future__ import annotations

from pathlib import Path

from embedder.formats.base import Format
from embedder.formats.markdown import MarkdownFormat
from embedder.formats.text import TextFormat
from embedder.formats.yaml import YamlFormat

_FORMATS: list[Format] = [
    MarkdownFormat(),
    YamlFormat(),
    TextFormat(),
]


def get_format(path: Path) -> Format:
    for fmt in _FORMATS:
        if fmt.matches(path):
            return fmt
    return TextFormat()
