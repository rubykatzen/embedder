from pathlib import Path

import pytest

from embedder.blocks import BlockUpdate, parse_blocks
from embedder.errors import EmbedderError
from embedder.providers import Provider
from embedder.providers.github import GitHubAssetRef, parse_github_ref
from embedder.providers.local import LocalProvider, LocalRef
from embedder.updater import check_blocks, update_files
from tests.helpers import close_marker, marker


class FakeGitHubProvider:
    def __init__(self) -> None:
        self.latest: dict[str, str] = {"rubykatzen/embedder": "v0.2.0"}
        self.assets: dict[str, str] = {
            "github.com/rubykatzen/embedder@v0.2.0:fragment.md": "new managed text\n",
        }
        self.resolve_calls = 0

    def matches(self, raw: str) -> bool:
        return raw.startswith("github.com/")

    def parse_ref(self, raw: str) -> GitHubAssetRef:
        return parse_github_ref(raw)

    def resolve(self, ref: GitHubAssetRef) -> GitHubAssetRef:
        self.resolve_calls += 1
        return ref.with_tag(self.latest[ref.repository])

    def resolve_cached(self, ref: GitHubAssetRef, cached: GitHubAssetRef) -> GitHubAssetRef:
        return ref.with_tag(cached.tag)

    def always_refresh(self, ref: GitHubAssetRef) -> bool:
        return False

    def fetch(self, ref: GitHubAssetRef, base_dir: Path) -> str:
        return self.assets[ref.render()]

    def cache_key(self, ref: GitHubAssetRef) -> str:
        return ref.repository


def fake_providers() -> list[Provider]:
    return [FakeGitHubProvider(), LocalProvider()]


def test_check_blocks_marks_updates() -> None:
    text = "\n".join(
        [
            marker("github.com/rubykatzen/embedder@v0.1.0:fragment.md"),
            "old",
            close_marker(),
            "",
        ]
    )
    blocks = parse_blocks(Path("AGENTS.md"), text)

    results = check_blocks(blocks, fake_providers())

    assert len(results) == 1
    assert results[0].latest_ref.render() == "github.com/rubykatzen/embedder@v0.2.0:fragment.md"
    assert results[0].update_available


def test_update_files_replaces_only_managed_body(tmp_path: Path) -> None:
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "\n".join(
            [
                "before",
                marker("github.com/rubykatzen/embedder@v0.1.0:fragment.md"),
                "old managed text",
                close_marker(),
                "after",
                "",
            ]
        ),
        encoding="utf-8",
    )

    changed = update_files([tmp_path], fake_providers())

    assert [item.path for item in changed] == [str(target)]
    assert target.read_text(encoding="utf-8") == "\n".join(
        [
            "before",
            marker("github.com/rubykatzen/embedder@v0.2.0:fragment.md"),
            "new managed text",
            close_marker(),
            "after",
            "",
        ]
    )


def test_apply_update_keeps_body_trailing_newline() -> None:
    text = "\n".join(
        [
            marker("github.com/rubykatzen/embedder@v0.1.0:fragment.md"),
            "old",
            close_marker(),
            "",
        ]
    )
    block = parse_blocks(Path("AGENTS.md"), text)[0]
    new_ref = block.ref.with_tag("v0.2.0")

    from embedder.blocks import apply_updates

    updated = apply_updates(
        Path("AGENTS.md"),
        text,
        [BlockUpdate(block=block, new_ref=new_ref, new_body="new")],
    )

    assert updated == "\n".join(
        [
            marker("github.com/rubykatzen/embedder@v0.2.0:fragment.md"),
            "new",
            close_marker(),
            "",
        ]
    )


def test_check_blocks_caches_resolve_per_repository() -> None:
    text = "\n".join(
        [
            marker("github.com/rubykatzen/embedder@v0.1.0:first.md"),
            "old",
            close_marker(),
            marker("github.com/rubykatzen/embedder@v0.1.0:second.md"),
            "old",
            close_marker(),
            "",
        ]
    )
    blocks = parse_blocks(Path("AGENTS.md"), text)
    provider = FakeGitHubProvider()

    check_blocks(blocks, [provider, LocalProvider()])

    assert provider.resolve_calls == 1


def test_local_ref_is_always_current(tmp_path: Path) -> None:
    fragment = tmp_path / "fragment.md"
    fragment.write_text("local content\n", encoding="utf-8")

    target = tmp_path / "README.md"
    target.write_text(
        "\n".join(
            [
                marker("local:fragment.md"),
                "old content",
                close_marker(),
                "",
            ]
        ),
        encoding="utf-8",
    )

    registry = [FakeGitHubProvider(), LocalProvider()]
    results = check_blocks(parse_blocks(target, target.read_text(encoding="utf-8")), registry)

    assert not results[0].update_available


def test_local_ref_fetch(tmp_path: Path) -> None:
    fragment = tmp_path / "frag.md"
    fragment.write_text("hello from local\n", encoding="utf-8")

    ref = LocalRef(path="frag.md")
    content = LocalProvider().fetch(ref, tmp_path)

    assert content == "hello from local\n"


def test_cache_uses_correct_asset_per_block() -> None:
    """Two blocks from the same repo must not share each other's asset."""
    text = "\n".join(
        [
            marker("github.com/rubykatzen/embedder@v0.1.0:first.md"),
            "old",
            close_marker(),
            marker("github.com/rubykatzen/embedder@v0.1.0:second.md"),
            "old",
            close_marker(),
            "",
        ]
    )
    blocks = parse_blocks(Path("AGENTS.md"), text)
    registry = [FakeGitHubProvider(), LocalProvider()]

    results = check_blocks(blocks, registry)

    assert results[0].latest_ref.render() == "github.com/rubykatzen/embedder@v0.2.0:first.md"
    assert results[1].latest_ref.render() == "github.com/rubykatzen/embedder@v0.2.0:second.md"


def test_local_ref_body_refreshed_on_update(tmp_path: Path) -> None:
    """update_files re-fetches local refs even when the ref itself hasn't changed."""
    fragment = tmp_path / "frag.md"
    fragment.write_text("v1 content\n", encoding="utf-8")

    target = tmp_path / "README.md"
    target.write_text(
        "\n".join([marker("local:frag.md"), "old content", close_marker(), ""]),
        encoding="utf-8",
    )

    fragment.write_text("v2 content\n", encoding="utf-8")
    registry = [FakeGitHubProvider(), LocalProvider()]
    update_files([tmp_path], registry)

    assert "v2 content" in target.read_text(encoding="utf-8")


def test_local_ref_path_traversal_rejected(tmp_path: Path) -> None:
    ref = LocalRef(path="../../etc/passwd")
    with pytest.raises(EmbedderError, match="escapes base directory"):
        LocalProvider().fetch(ref, tmp_path)


def test_default_providers_not_mutated_between_calls() -> None:
    from embedder.providers import DEFAULT_PROVIDERS

    text = "\n".join(
        [
            marker("github.com/rubykatzen/embedder@v0.1.0:fragment.md"),
            "old",
            close_marker(),
            "",
        ]
    )
    blocks = parse_blocks(Path("AGENTS.md"), text)

    providers_before = list(DEFAULT_PROVIDERS)
    check_blocks(blocks, fake_providers())
    check_blocks(blocks, fake_providers())
    assert list(DEFAULT_PROVIDERS) == providers_before
