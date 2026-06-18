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
from embedder.github import GitHubClient


@dataclass(frozen=True)
class CheckResult:
    block: EmbedderBlock
    latest_tag: str

    @property
    def update_available(self) -> bool:
        return self.block.ref.tag != self.latest_tag


@dataclass(frozen=True)
class FileUpdate:
    path: str
    changed_blocks: list[CheckResult]


def check_blocks(blocks: list[EmbedderBlock], github: GitHubClient) -> list[CheckResult]:
    latest_by_repository: dict[str, str] = {}
    results: list[CheckResult] = []

    for block in blocks:
        latest = latest_by_repository.get(block.ref.repository)
        if latest is None:
            latest = github.latest_tag(block.ref)
            latest_by_repository[block.ref.repository] = latest
        results.append(CheckResult(block=block, latest_tag=latest))

    return results


def update_files(paths: list[Path], github: GitHubClient) -> list[FileUpdate]:
    changed: list[FileUpdate] = []

    for path in iter_files(paths):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        blocks = parse_blocks(path, text)
        if not blocks:
            continue

        checks = check_blocks(blocks, github)
        updates: list[BlockUpdate] = []
        changed_checks: list[CheckResult] = []
        for check in checks:
            if not check.update_available:
                continue
            new_ref = check.block.ref.with_tag(check.latest_tag)
            new_body = github.download_asset(new_ref)
            updates.append(
                BlockUpdate(block=check.block, new_ref=new_ref, new_body=new_body)
            )
            changed_checks.append(check)

        if not updates:
            continue

        new_text = apply_updates(text, updates)
        if new_text == text:
            continue
        path.write_text(new_text, encoding="utf-8")
        changed.append(FileUpdate(path=str(path), changed_blocks=changed_checks))

    return changed
