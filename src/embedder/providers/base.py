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

    def resolve_cached(self, ref: AnyRef, cached: AnyRef) -> AnyRef:
        """Apply the version from a previously resolved ref to a different ref.

        Used to reuse a cached provider lookup (e.g. latest tag) for a block
        with the same cache key but a different asset or path.
        """
        ...

    def always_refresh(self, ref: AnyRef) -> bool:
        """Return True if this ref should always be re-fetched on update,
        even when resolve() reports no version change."""
        ...

    def fetch(self, ref: AnyRef, base_dir: Path) -> str:
        """Return the fragment content."""
        ...

    def cache_key(self, ref: AnyRef) -> str | None:
        """Deduplication key for resolve() calls. None means no caching."""
        ...
