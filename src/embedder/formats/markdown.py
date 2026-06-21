from __future__ import annotations

import re
from pathlib import Path

OPEN_RE = re.compile(r"^\s*<!--\s+embedder\s+(?P<ref>\S+)\s+-->\s*$")
CLOSE_RE = re.compile(r"^\s*<!--\s+/embedder\s+-->\s*$")
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


class MarkdownFormat:
    @property
    def open_re(self) -> re.Pattern[str]:
        return OPEN_RE

    @property
    def close_re(self) -> re.Pattern[str]:
        return CLOSE_RE

    def matches(self, path: Path) -> bool:
        return path.suffix.lower() in {".md", ".markdown"}

    def make_scanner(self) -> _MarkdownScanner:
        return _MarkdownScanner()

    def render_open(self, ref_str: str) -> str:
        return f"<!-- embedder {ref_str} -->"

    def render_close(self) -> str:
        return "<!-- /embedder -->"
