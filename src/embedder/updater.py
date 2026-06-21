from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from embedder.blocks import (
    BlockUpdate,
    EmbedderBlock,
    apply_updates,
    iter_files,
    parse_blocks,
)
from embedder.providers import DEFAULT_REGISTRY, AnyRef, ProviderRegistry


@dataclass(frozen=True)
class CheckResult:
    block: EmbedderBlock
    latest_ref: AnyRef

    @property
    def update_available(self) -> bool:
        return self.block.ref != self.latest_ref


@dataclass(frozen=True)
class FileUpdate:
    path: str
    changed_blocks: list[CheckResult]


def check_blocks(
    blocks: list[EmbedderBlock],
    registry: ProviderRegistry = DEFAULT_REGISTRY,
) -> list[CheckResult]:
    cache: dict[str, AnyRef] = {}
    results: list[CheckResult] = []

    for block in blocks:
        provider = registry.get(block.ref.render())
        key = provider.cache_key(block.ref)
        if key is not None:
            latest = cache.get(key)
            if latest is None:
                latest = provider.resolve(block.ref)
                cache[key] = latest
        else:
            latest = provider.resolve(block.ref)
        results.append(CheckResult(block=block, latest_ref=latest))

    return results


def update_files(
    paths: list[Path],
    registry: ProviderRegistry = DEFAULT_REGISTRY,
) -> list[FileUpdate]:
    changed: list[FileUpdate] = []

    for path in iter_files(paths):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        blocks = parse_blocks(path, text)
        if not blocks:
            continue

        checks = check_blocks(blocks, registry)
        updates: list[BlockUpdate] = []
        changed_checks: list[CheckResult] = []

        for check in checks:
            if not check.update_available:
                continue
            provider = registry.get(check.latest_ref.render())
            new_body = provider.fetch(check.latest_ref, path.parent)
            updates.append(
                BlockUpdate(block=check.block, new_ref=check.latest_ref, new_body=new_body)
            )
            changed_checks.append(check)

        if not updates:
            continue

        new_text = apply_updates(path, text, updates)
        if new_text == text:
            continue
        path.write_text(new_text, encoding="utf-8")
        changed.append(FileUpdate(path=str(path), changed_blocks=changed_checks))

    return changed
