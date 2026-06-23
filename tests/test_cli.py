from pathlib import Path

from embedder.cli import ExitCode, main
from tests.helpers import close_marker, marker


def test_scan_prints_blocks(tmp_path: Path, capsys) -> None:
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "\n".join(
            [
                "# AGENTS.md",
                "",
                marker("github.com/rubykatzen/embedder@v0.1.0:fragment.md"),
                "managed",
                close_marker(),
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert main(["scan", str(tmp_path)]) == int(ExitCode.OK)

    captured = capsys.readouterr()
    assert "AGENTS.md:3 github.com/rubykatzen/embedder:fragment.md" in captured.out


def test_scan_json(tmp_path: Path, capsys) -> None:
    target = tmp_path / "README.md"
    target.write_text(
        "\n".join(
            [
                marker("github.com/rubykatzen/embedder@v0.1.0:fragment.md"),
                "managed",
                close_marker(),
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert main(["scan", "--json", str(target)]) == int(ExitCode.OK)

    captured = capsys.readouterr()
    assert '"blocks"' in captured.out
    assert '"asset": "fragment.md"' in captured.out


def test_check_missing_gh_returns_environment_error(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "\n".join(
            [
                marker("github.com/rubykatzen/embedder@v0.1.0:fragment.md"),
                "managed",
                close_marker(),
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PATH", "")

    assert main(["check", str(target)]) == int(ExitCode.ENVIRONMENT)

    captured = capsys.readouterr()
    assert "Required executable is missing: gh" in captured.err
