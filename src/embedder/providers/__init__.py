from __future__ import annotations

from embedder.providers.base import Provider
from embedder.providers.github import GitHubProvider
from embedder.providers.local import LocalProvider, LocalRef
from embedder.refs import GitHubAssetRef, RefError

AnyRef = GitHubAssetRef | LocalRef


class ProviderRegistry:
    def __init__(self, providers: list[Provider]) -> None:
        self._providers = providers

    def get(self, raw: str) -> Provider:
        for provider in self._providers:
            if provider.matches(raw):
                return provider
        raise RefError(f"Unknown ref scheme: {raw!r}")

    def parse_ref(self, raw: str) -> AnyRef:
        return self.get(raw).parse_ref(raw)


DEFAULT_REGISTRY = ProviderRegistry([GitHubProvider(), LocalProvider()])


def parse_ref(raw: str) -> AnyRef:
    return DEFAULT_REGISTRY.parse_ref(raw)
