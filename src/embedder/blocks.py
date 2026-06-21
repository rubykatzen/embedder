from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from embedder.refs import RefError

SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
    "vendor",
}


class EmbedderError(Exception):
    pass


class EmbedderEnvironmentError(EmbedderError):
    pass


@dataclass(frozen=True)
class EmbedderBlock:
    path: str
    start_line: int
    end_line: int
    ref: object  # AnyRef — typed as object to avoid circular import
    body: str


@dataclass(frozen=True)
class BlockUpdate:
    block: EmbedderBlock
    new_ref: object  # AnyRef
    new_body: str


def parse_blocks(path: Path, text: str) -> list[EmbedderBlock]:
    from embedder.formats import get_format
    from embedder.providers import parse_ref

    fmt = get_format(path)
    scanner = fmt.make_scanner()
    lines = text.splitlines(keepends=True)
    blocks: list[EmbedderBlock] = []
    active_start: int | None = None
    active_ref = None
    body_start = 0

    for index, line in enumerate(lines):
        if active_start is None and scanner.advance(line):
            continue

        open_match = fmt.open_re.match(line)
        if open_match:
            if active_start is not None:
                raise EmbedderError(
                    f"{path}:{index + 1}: nested embedder block is not allowed"
                )
            try:
                active_ref = parse_ref(open_match["ref"])
            except RefError as error:
                raise EmbedderError(f"{path}:{index + 1}: {error}") from error
            active_start = index
            body_start = index + 1
            continue

        if fmt.close_re.match(line):
            if active_start is None or active_ref is None:
                raise EmbedderError(
                    f"{path}:{index + 1}: closing embedder marker without opening marker"
                )
            blocks.append(
                EmbedderBlock(
                    path=str(path),
                    start_line=active_start + 1,
                    end_line=index + 1,
                    ref=active_ref,
                    body="".join(lines[body_start:index]),
                )
            )
            active_start = None
            active_ref = None

    if active_start is not None:
        raise EmbedderError(f"{path}:{active_start + 1}: unclosed embedder block")

    return blocks


def is_probably_text(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(4096)
    except OSError:
        return False
    return b"\0" not in chunk


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            files.append(path)
            continue
        if not path.is_dir():
            raise EmbedderError(f"Path does not exist: {path}")
        for root, dirs, filenames in os.walk(path):
            dirs[:] = [dirname for dirname in dirs if dirname not in SKIP_DIRS]
            for filename in filenames:
                files.append(Path(root) / filename)
    return sorted(files)


def scan_paths(paths: list[Path]) -> list[EmbedderBlock]:
    blocks: list[EmbedderBlock] = []
    for path in iter_files(paths):
        if not is_probably_text(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as error:
            raise EmbedderError(f"Could not read {path}: {error}") from error
        blocks.extend(parse_blocks(path, text))
    return blocks


def apply_updates(path: Path, text: str, updates: list[BlockUpdate]) -> str:
    from embedder.formats import get_format

    if not updates:
        return text

    fmt = get_format(path)
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    cursor = 0

    for update in sorted(updates, key=lambda item: item.block.start_line):
        start = update.block.start_line - 1
        end = update.block.end_line - 1
        if start < cursor:
            raise EmbedderError("Overlapping embedder block updates")

        original_open = lines[start]
        newline = "\n" if original_open.endswith("\n") else ""
        indent = original_open[: len(original_open) - len(original_open.lstrip())]
        replacement_body = update.new_body
        if replacement_body and not replacement_body.endswith("\n"):
            replacement_body += "\n"

        output.extend(lines[cursor:start])
        output.append(f"{indent}{fmt.render_open(update.new_ref.render())}{newline}")
        output.append(replacement_body)
        output.append(lines[end])
        cursor = end + 1

    output.extend(lines[cursor:])
    return "".join(output)
