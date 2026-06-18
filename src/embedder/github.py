from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from embedder.blocks import EmbedderEnvironmentError, EmbedderError
from embedder.refs import GitHubAssetRef


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class GitHubClient:
    def available(self) -> bool:
        return shutil.which("gh") is not None

    def require(self) -> None:
        if not self.available():
            raise EmbedderEnvironmentError("Required executable is missing: gh")

    def run(self, args: list[str], *, check: bool = True) -> CommandResult:
        self.require()
        proc = subprocess.run(
            ["gh", *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if check and proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip()
            raise EmbedderError(f"Command failed: gh {' '.join(args)}\n{detail}")
        return CommandResult(
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )

    def auth_ok(self) -> bool:
        return self.run(["auth", "status"], check=False).returncode == 0

    def latest_tag(self, ref: GitHubAssetRef) -> str:
        result = self.run(
            [
                "release",
                "view",
                "--repo",
                ref.repository,
                "--json",
                "tagName",
                "--jq",
                ".tagName",
            ]
        )
        if not result.stdout or result.stdout == "null":
            raise EmbedderError(f"Could not resolve latest release for {ref.repository}")
        return result.stdout

    def download_asset(self, ref: GitHubAssetRef) -> str:
        with tempfile.TemporaryDirectory(prefix="embedder-") as tmpdir:
            self.run(
                [
                    "release",
                    "download",
                    ref.tag,
                    "--repo",
                    ref.repository,
                    "--pattern",
                    ref.asset,
                    "--dir",
                    tmpdir,
                ]
            )
            path = Path(tmpdir) / ref.asset
            if not path.is_file():
                raise EmbedderError(f"Release asset not found: {ref.render()}")
            return path.read_text(encoding="utf-8")
