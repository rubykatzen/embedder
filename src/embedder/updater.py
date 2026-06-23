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
from embedder.providers import DEFAULT_PROVIDERS, AnyRef, Provider, get_provider
from embedder.providers.local import LocalProvider


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
    providers: list[Provider] | None = None,
) -> list[CheckResult]:
    _providers = providers if providers is not None else DEFAULT_PROVIDERS
    resolved_cache: dict[str, AnyRef] = {}
    results: list[CheckResult] = []

    for block in blocks:
        provider = get_provider(block.ref.render(), _providers)
        key = provider.cache_key(block.ref)
        if key is not None:
            if key in resolved_cache:
                latest = provider.resolve_cached(block.ref, resolved_cache[key])
            else:
                latest = provider.resolve(block.ref)
                resolved_cache[key] = latest
        else:
            latest = provider.resolve(block.ref)
        results.append(CheckResult(block=block, latest_ref=latest))

    return results


def update_files(
    paths: list[Path],
    providers: list[Provider] | None = None,
    *,
    local_only: bool = False,
    base_dir: Path | None = None,
) -> list[FileUpdate]:
    _providers = providers if providers is not None else DEFAULT_PROVIDERS
    _base_dir = base_dir if base_dir is not None else Path.cwd()
    changed: list[FileUpdate] = []

    for path in iter_files(paths):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        blocks = parse_blocks(path, text, _providers)
        if not blocks:
            continue

        checks = check_blocks(blocks, _providers) if not local_only else [
            CheckResult(block=block, latest_ref=block.ref) for block in blocks
        ]
        updates: list[BlockUpdate] = []
        changed_checks: list[CheckResult] = []

        for check in checks:
            provider = get_provider(check.block.ref.render(), _providers)
            if local_only and not isinstance(provider, LocalProvider):
                continue
            if not check.update_available and not provider.always_refresh(check.block.ref):
                continue
            new_body = provider.fetch(check.latest_ref, _base_dir)
            if new_body == check.block.body and not check.update_available:
                continue
            updates.append(
                BlockUpdate(block=check.block, new_ref=check.block.ref, new_body=new_body)
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
