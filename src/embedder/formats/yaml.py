from __future__ import annotations

import re
from pathlib import Path

OPEN_RE = re.compile(r"^\s*#\s+embedder\s+(?P<ref>\S+)\s*$")
CLOSE_RE = re.compile(r"^\s*#\s+/embedder\s*$")

# Matches the start of a block scalar (key: | or key: >), capturing indentation level.
_BLOCK_SCALAR_RE = re.compile(r"^(?P<indent>\s*)\S.*:\s*[|>][+-]?\s*$")


class _YamlScanner:
    """Skips lines inside YAML block scalars to prevent false-positive marker detection."""

    def __init__(self) -> None:
        self._block_indent: int | None = None

    def advance(self, line: str) -> bool:
        stripped = line.rstrip("\n")

        if self._block_indent is not None:
            if not stripped:
                # Blank lines are valid inside a block scalar.
                return True
            if not stripped[0].isspace():
                self._block_indent = None
            elif len(stripped) - len(stripped.lstrip()) > self._block_indent:
                return True
            else:
                self._block_indent = None

        m = _BLOCK_SCALAR_RE.match(stripped)
        if m:
            self._block_indent = len(m["indent"])

        return False


class YamlFormat:
    @property
    def open_re(self) -> re.Pattern[str]:
        return OPEN_RE

    @property
    def close_re(self) -> re.Pattern[str]:
        return CLOSE_RE

    def matches(self, path: Path) -> bool:
        return path.suffix.lower() in {".yml", ".yaml"}

    def make_scanner(self) -> _YamlScanner:
        return _YamlScanner()

    def render_open(self, ref_str: str) -> str:
        return f"# embedder {ref_str}"

    def render_close(self) -> str:
        return "# /embedder"
