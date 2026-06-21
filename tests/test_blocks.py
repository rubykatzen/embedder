from pathlib import Path

import pytest

from embedder.blocks import BlockUpdate, apply_updates, parse_blocks
from embedder.errors import EmbedderError
from tests.helpers import close_marker, marker, yaml_close_marker, yaml_marker


def test_parse_single_block() -> None:
    text = "\n".join(
        [
            "before",
            marker("github.com/rubykatzen/embedder@v0.1.0:fragment.md"),
            "managed",
            "text",
            close_marker(),
            "after",
            "",
        ]
    )

    blocks = parse_blocks(Path("AGENTS.md"), text)

    assert len(blocks) == 1
    block = blocks[0]
    assert block.path == "AGENTS.md"
    assert block.start_line == 2
    assert block.end_line == 5
    assert block.body == "managed\ntext\n"
    assert block.ref.repository == "rubykatzen/embedder"
    assert block.ref.tag == "v0.1.0"
    assert block.ref.asset == "fragment.md"


def test_parse_multiple_blocks() -> None:
    text = "\n".join(
        [
            marker("github.com/a/b@v1:first.md"),
            "one",
            close_marker(),
            "local",
            marker("github.com/c/d@v2:second.md"),
            "two",
            close_marker(),
            "",
        ]
    )

    blocks = parse_blocks(Path("README.md"), text)

    assert [block.ref.render() for block in blocks] == [
        "github.com/a/b@v1:first.md",
        "github.com/c/d@v2:second.md",
    ]


def test_reject_unclosed_block() -> None:
    text = marker("github.com/rubykatzen/embedder@v0.1.0:fragment.md") + "\n"

    with pytest.raises(EmbedderError, match="unclosed"):
        parse_blocks(Path("AGENTS.md"), text)


def test_reject_orphan_closing_marker() -> None:
    with pytest.raises(EmbedderError, match="without opening"):
        parse_blocks(Path("AGENTS.md"), close_marker() + "\n")


def test_reject_nested_blocks() -> None:
    text = "\n".join(
        [
            marker("github.com/a/b@v1:first.md"),
            marker("github.com/c/d@v2:second.md"),
            close_marker(),
            "",
        ]
    )

    with pytest.raises(EmbedderError, match="nested"):
        parse_blocks(Path("AGENTS.md"), text)


def test_ignore_markers_inside_markdown_code_fence() -> None:
    text = "\n".join(
        [
            "```markdown",
            marker("github.com/rubykatzen/embedder@v0.1.0:fragment.md"),
            "managed",
            close_marker(),
            "```",
            "",
        ]
    )

    assert parse_blocks(Path("README.md"), text) == []


def test_parse_yaml_block() -> None:
    text = "\n".join(
        [
            "before: value",
            yaml_marker("local:fragments/config.yaml"),
            "key: managed",
            yaml_close_marker(),
            "after: value",
            "",
        ]
    )

    blocks = parse_blocks(Path("config.yaml"), text)

    assert len(blocks) == 1
    block = blocks[0]
    assert block.ref.render() == "local:fragments/config.yaml"
    assert block.body == "key: managed\n"


def test_yaml_ignores_markers_in_block_scalar() -> None:
    text = "\n".join(
        [
            "description: |",
            f"  {yaml_marker('local:file.yaml')}",
            "  some content",
            f"  {yaml_close_marker()}",
            "other: value",
            "",
        ]
    )

    assert parse_blocks(Path("config.yaml"), text) == []


def test_yaml_ignores_markers_after_blank_line_in_block_scalar() -> None:
    text = "\n".join(
        [
            "description: |",
            "  first paragraph",
            "",
            f"  {yaml_marker('local:file.yaml')}",
            "  second paragraph",
            f"  {yaml_close_marker()}",
            "other: value",
            "",
        ]
    )

    assert parse_blocks(Path("config.yaml"), text) == []


def test_yaml_ignores_markers_in_block_scalar_with_indent_indicator() -> None:
    text = "\n".join(
        [
            "description: |2",
            f"  {yaml_marker('local:file.yaml')}",
            "other: value",
            "",
        ]
    )

    assert parse_blocks(Path("config.yaml"), text) == []


def test_yaml_ignores_markers_in_block_scalar_with_trailing_comment() -> None:
    text = "\n".join(
        [
            "description: | # inline comment",
            f"  {yaml_marker('local:file.yaml')}",
            "other: value",
            "",
        ]
    )

    assert parse_blocks(Path("config.yaml"), text) == []


def test_parse_local_ref_in_markdown() -> None:
    text = "\n".join(
        [
            marker("local:fragments/file.md"),
            "managed content",
            close_marker(),
            "",
        ]
    )

    blocks = parse_blocks(Path("README.md"), text)

    assert len(blocks) == 1
    assert blocks[0].ref.render() == "local:fragments/file.md"


def test_yaml_ignores_markers_in_sequence_block_scalar() -> None:
    text = "\n".join(
        [
            "items:",
            "  - |",
            f"    {yaml_marker('local:file.yaml')}",
            "    some content",
            f"    {yaml_close_marker()}",
            "other: value",
            "",
        ]
    )

    assert parse_blocks(Path("config.yaml"), text) == []


def test_parse_blocks_uses_injected_providers() -> None:
    from dataclasses import dataclass
    from pathlib import Path as _Path

    @dataclass(frozen=True)
    class FakeRef:
        name: str

        def render(self) -> str:
            return f"fake:{self.name}"

    class FakeProvider:
        def matches(self, raw: str) -> bool:
            return raw.startswith("fake:")

        def parse_ref(self, raw: str) -> FakeRef:
            return FakeRef(name=raw[len("fake:"):])

        def resolve(self, ref: FakeRef) -> FakeRef:
            return ref

        def resolve_cached(self, ref: FakeRef, cached: FakeRef) -> FakeRef:
            return ref

        def always_refresh(self, ref: FakeRef) -> bool:
            return False

        def fetch(self, ref: FakeRef, base_dir: _Path) -> str:
            return ""

        def cache_key(self, ref: FakeRef) -> str | None:
            return None

    text = "\n".join(
        [
            marker("fake:thing"),
            "body",
            close_marker(),
            "",
        ]
    )

    with pytest.raises(EmbedderError):
        parse_blocks(Path("README.md"), text)

    blocks = parse_blocks(Path("README.md"), text, providers=[FakeProvider()])
    assert len(blocks) == 1
    assert blocks[0].ref.render() == "fake:thing"


def test_apply_updates_indents_body_to_match_yaml_marker() -> None:
    text = "\n".join(
        [
            "parent:",
            f"  {yaml_marker('local:frag.yaml')}",
            "  old: value",
            f"  {yaml_close_marker()}",
            "",
        ]
    )
    path = Path("config.yaml")
    block = parse_blocks(path, text)[0]

    updated = apply_updates(
        path,
        text,
        [BlockUpdate(block=block, new_ref=block.ref, new_body="new: value\n")],
    )

    assert updated == "\n".join(
        [
            "parent:",
            f"  {yaml_marker('local:frag.yaml')}",
            "  new: value",
            f"  {yaml_close_marker()}",
            "",
        ]
    )
