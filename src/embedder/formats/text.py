from __future__ import annotations

import re
from pathlib import Path


OPEN_RE = re.compile(r"^\s*<!--\s+embedder\s+(?P<ref>\S+)\s+-->\s*$")
CLOSE_RE = re.compile(r"^\s*<!--\s+/embedder\s+-->\s*$")


class _NoopScanner:
    def advance(self, line: str) -> bool:
        return False


class TextFormat:
    @property
    def open_re(self) -> re.Pattern[str]:
        return OPEN_RE

    @property
    def close_re(self) -> re.Pattern[str]:
        return CLOSE_RE

    def matches(self, path: Path) -> bool:
        return True

    def make_scanner(self) -> _NoopScanner:
        return _NoopScanner()

    def render_open(self, ref_str: str) -> str:
        return f"<!-- embedder {ref_str} -->"

    def render_close(self) -> str:
        return "<!-- /embedder -->"
