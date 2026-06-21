from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from embedder.providers import AnyRef


@runtime_checkable
class Provider(Protocol):
    def matches(self, raw: str) -> bool: ...

    def parse_ref(self, raw: str) -> AnyRef: ...

    def resolve(self, ref: AnyRef) -> AnyRef:
        """Return the ref updated to the latest available version."""
        ...

    def fetch(self, ref: AnyRef, base_dir: Path) -> str:
        """Return the fragment content."""
        ...

    def cache_key(self, ref: AnyRef) -> str | None:
        """Deduplication key for resolve() calls. None means no caching."""
        ...
