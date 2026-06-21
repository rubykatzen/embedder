from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from embedder.errors import EmbedderError, RefError


@dataclass(frozen=True)
class LocalRef:
    path: str

    def render(self) -> str:
        return f"local:{self.path}"


class LocalProvider:
    def matches(self, raw: str) -> bool:
        return raw.startswith("local:")

    def parse_ref(self, raw: str) -> LocalRef:
        path = raw[len("local:"):]
        if not path:
            raise RefError("local: ref must specify a path")
        return LocalRef(path=path)

    def resolve(self, ref: LocalRef) -> LocalRef:
        return ref

    def resolve_cached(self, ref: LocalRef, cached: LocalRef) -> LocalRef:
        return ref

    def always_refresh(self, ref: LocalRef) -> bool:
        return True

    def fetch(self, ref: LocalRef, base_dir: Path) -> str:
        resolved_base = base_dir.resolve()
        target = (base_dir / ref.path).resolve()
        if not target.is_relative_to(resolved_base):
            raise EmbedderError(
                f"Local fragment path escapes base directory: {ref.path!r}"
            )
        if not target.is_file():
            raise EmbedderError(f"Local fragment not found: {target}")
        return target.read_text(encoding="utf-8")

    def cache_key(self, ref: LocalRef) -> str | None:
        return None
