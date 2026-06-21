from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class LineScanner(Protocol):
    def advance(self, line: str) -> bool:
        """Advance by one line. Returns True if the line should be skipped."""
        ...


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
