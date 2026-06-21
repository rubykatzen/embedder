from __future__ import annotations

import re
from pathlib import Path

from embedder.formats.text import TextFormat


FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})")


class _MarkdownScanner:
    def __init__(self) -> None:
        self._fence: str | None = None

    def advance(self, line: str) -> bool:
        m = FENCE_RE.match(line)
        if m:
            marker = m["fence"][0]
            if self._fence is None:
                self._fence = marker
            elif self._fence == marker:
                self._fence = None
            return True
        return self._fence is not None


class MarkdownFormat(TextFormat):
    def matches(self, path: Path) -> bool:
        return path.suffix.lower() in {".md", ".markdown"}

    def make_scanner(self) -> _MarkdownScanner:
        return _MarkdownScanner()
