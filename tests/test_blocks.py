from pathlib import Path

import pytest

from embedder.blocks import EmbedderError, parse_blocks
from tests.helpers import close_marker, marker


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
