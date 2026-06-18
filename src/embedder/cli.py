from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from enum import IntEnum
from pathlib import Path
from typing import Any

from embedder import __version__
from embedder.blocks import (
    EmbedderBlock,
    EmbedderEnvironmentError,
    EmbedderError,
    scan_paths,
)
from embedder.github import GitHubClient
from embedder.updater import check_blocks, update_files


class ExitCode(IntEnum):
    OK = 0
    UPDATES_AVAILABLE = 1
    ENVIRONMENT = 3
    COMMAND_FAILED = 4


def to_json(data: Any) -> None:
    def default(value: Any) -> Any:
        if hasattr(value, "__dataclass_fields__"):
            return asdict(value)
        if isinstance(value, Path):
            return str(value)
        raise TypeError(f"Object is not JSON serializable: {value!r}")

    print(json.dumps(data, indent=2, sort_keys=True, default=default))


def command_scan(args: argparse.Namespace) -> int:
    blocks = scan_paths([Path(path) for path in args.paths])
    if args.json:
        to_json({"blocks": blocks})
        return int(ExitCode.OK)

    if not blocks:
        print("No embedder blocks found.")
        return int(ExitCode.OK)

    for block in blocks:
        ref = block.ref
        print(
            f"{block.path}:{block.start_line} "
            f"{ref.owner}/{ref.repo}@{ref.tag}:{ref.asset}"
        )
    return int(ExitCode.OK)


def print_block(block: EmbedderBlock, *, latest_tag: str | None = None) -> None:
    ref = block.ref
    suffix = "" if latest_tag is None else f" -> {latest_tag}"
    print(
        f"{block.path}:{block.start_line} "
        f"{ref.owner}/{ref.repo}@{ref.tag}:{ref.asset}{suffix}"
    )


def command_check(args: argparse.Namespace) -> int:
    blocks = scan_paths([Path(path) for path in args.paths])
    results = check_blocks(blocks, GitHubClient())
    updates = [result for result in results if result.update_available]

    if args.json:
        to_json({"updates": updates, "blocks": results})
        return int(ExitCode.UPDATES_AVAILABLE if updates else ExitCode.OK)

    if not blocks:
        print("No embedder blocks found.")
        return int(ExitCode.OK)
    if not updates:
        print("All embedder blocks are up to date.")
        return int(ExitCode.OK)

    for result in updates:
        print_block(result.block, latest_tag=result.latest_tag)
    return int(ExitCode.UPDATES_AVAILABLE)


def command_update(args: argparse.Namespace) -> int:
    changed = update_files([Path(path) for path in args.paths], GitHubClient())
    if args.json:
        to_json({"changed": changed})
        return int(ExitCode.OK)
    if not changed:
        print("No embedder blocks changed.")
        return int(ExitCode.OK)
    for file_update in changed:
        for result in file_update.changed_blocks:
            print_block(result.block, latest_tag=result.latest_tag)
    return int(ExitCode.OK)


def command_doctor(args: argparse.Namespace) -> int:
    github = GitHubClient()
    gh_available = github.available()
    checks = {
        "gh": "ok" if gh_available else "missing",
        "gh_auth": "ok" if gh_available and github.auth_ok() else "failed",
    }
    ok = all(value == "ok" for value in checks.values())
    if args.json:
        to_json({"ok": ok, "checks": checks})
    else:
        for name, value in checks.items():
            print(f"{name}: {value}")
        print(f"doctor: {'ok' if ok else 'failed'}")
    return int(ExitCode.OK if ok else ExitCode.ENVIRONMENT)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="embedder",
        description="Dependency-style updater for embedded text snippets.",
    )
    root.add_argument("-v", "--version", action="version", version=f"embedder {__version__}")
    subparsers = root.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Find managed embedder blocks.")
    scan.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to scan. Defaults to the current directory.",
    )
    scan.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    scan.set_defaults(func=command_scan)

    check = subparsers.add_parser("check", help="Check managed blocks for newer releases.")
    check.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to check. Defaults to the current directory.",
    )
    check.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    check.set_defaults(func=command_check)

    update = subparsers.add_parser("update", help="Update managed blocks in place.")
    update.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to update. Defaults to the current directory.",
    )
    update.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    update.set_defaults(func=command_update)

    doctor = subparsers.add_parser("doctor", help="Check local embedder prerequisites.")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    doctor.set_defaults(func=command_doctor)

    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.func(args))
    except EmbedderEnvironmentError as error:
        print(str(error), file=sys.stderr)
        return int(ExitCode.ENVIRONMENT)
    except EmbedderError as error:
        print(str(error), file=sys.stderr)
        return int(ExitCode.COMMAND_FAILED)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return int(ExitCode.COMMAND_FAILED)


if __name__ == "__main__":
    raise SystemExit(main())
