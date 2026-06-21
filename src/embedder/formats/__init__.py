from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol, runtime_checkable

from embedder.formats.markdown import MarkdownFormat
from embedder.formats.yaml import YamlFormat


@runtime_checkable
class LineScanner(Protocol):
    def advance(self, line: str) -> bool: ...


@runtime_checkable
class Format(Protocol):
    @property
    def open_re(self) -> re.Pattern[str]: ...

    @property
    def close_re(self) -> re.Pattern[str]: ...

    def matches(self, path: Path) -> bool: ...

    def make_scanner(self) -> LineScanner: ...

    def render_open(self, ref_str: str) -> str: ...

    def render_close(self) -> str: ...


_FORMATS: list[Format] = [
    MarkdownFormat(),
    YamlFormat(),
]


def get_format(path: Path) -> Format | None:
    for fmt in _FORMATS:
        if fmt.matches(path):
            return fmt
    return None
