from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from embedder.errors import RefError
from embedder.providers.github import GitHubAssetRef, GitHubProvider
from embedder.providers.local import LocalProvider, LocalRef

AnyRef = GitHubAssetRef | LocalRef


@runtime_checkable
class Provider(Protocol):
    def matches(self, raw: str) -> bool: ...

    def parse_ref(self, raw: str) -> AnyRef: ...

    def resolve(self, ref: AnyRef) -> AnyRef: ...

    def resolve_cached(self, ref: AnyRef, cached: AnyRef) -> AnyRef: ...

    def always_refresh(self, ref: AnyRef) -> bool: ...

    def fetch(self, ref: AnyRef, base_dir: Path) -> str: ...

    def cache_key(self, ref: AnyRef) -> str | None: ...


DEFAULT_PROVIDERS: list[Provider] = [GitHubProvider(), LocalProvider()]


def get_provider(raw: str, providers: list[Provider] | None = None) -> Provider:
    _providers = providers if providers is not None else DEFAULT_PROVIDERS
    for provider in _providers:
        if provider.matches(raw):
            return provider
    raise RefError(f"Unknown ref scheme: {raw!r}")


def parse_ref(raw: str) -> AnyRef:
    return get_provider(raw).parse_ref(raw)
