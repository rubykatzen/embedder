from pathlib import Path

from embedder.blocks import BlockUpdate, parse_blocks
from embedder.updater import check_blocks, update_files
from tests.helpers import close_marker, marker


class FakeGitHub:
    def __init__(self) -> None:
        self.latest = {
            "rubykatzen/embedder": "v0.2.0",
        }
        self.assets = {
            "github.com/rubykatzen/embedder@v0.2.0:snippet.md": "new managed text\n",
        }

    def latest_tag(self, ref) -> str:
        return self.latest[ref.repository]

    def download_asset(self, ref) -> str:
        return self.assets[ref.render()]


def test_check_blocks_marks_updates() -> None:
    text = "\n".join(
        [
            marker("github.com/rubykatzen/embedder@v0.1.0:snippet.md"),
            "old",
            close_marker(),
            "",
        ]
    )
    blocks = parse_blocks(Path("AGENTS.md"), text)

    results = check_blocks(blocks, FakeGitHub())

    assert len(results) == 1
    assert results[0].latest_tag == "v0.2.0"
    assert results[0].update_available


def test_update_files_replaces_only_managed_body(tmp_path: Path) -> None:
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "\n".join(
            [
                "before",
                marker("github.com/rubykatzen/embedder@v0.1.0:snippet.md"),
                "old managed text",
                close_marker(),
                "after",
                "",
            ]
        ),
        encoding="utf-8",
    )

    changed = update_files([tmp_path], FakeGitHub())

    assert [item.path for item in changed] == [str(target)]
    assert target.read_text(encoding="utf-8") == "\n".join(
        [
            "before",
            marker("github.com/rubykatzen/embedder@v0.2.0:snippet.md"),
            "new managed text",
            close_marker(),
            "after",
            "",
        ]
    )


def test_apply_update_keeps_body_trailing_newline() -> None:
    text = "\n".join(
        [
            marker("github.com/rubykatzen/embedder@v0.1.0:snippet.md"),
            "old",
            close_marker(),
            "",
        ]
    )
    block = parse_blocks(Path("AGENTS.md"), text)[0]
    new_ref = block.ref.with_tag("v0.2.0")

    from embedder.blocks import apply_updates

    updated = apply_updates(text, [BlockUpdate(block=block, new_ref=new_ref, new_body="new")])

    assert updated == "\n".join(
        [
            marker("github.com/rubykatzen/embedder@v0.2.0:snippet.md"),
            "new",
            close_marker(),
            "",
        ]
    )
