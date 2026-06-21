from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from embedder.errors import EmbedderEnvironmentError, EmbedderError, RefError

_REF_RE = re.compile(
    r"^github\.com/"
    r"(?P<owner>[A-Za-z0-9_.-]+)/"
    r"(?P<repo>[A-Za-z0-9_.-]+)"
    r"@(?P<tag>[^:\s]+)"
    r":(?P<asset>[^\s]+)$"
)


@dataclass(frozen=True)
class GitHubAssetRef:
    owner: str
    repo: str
    tag: str
    asset: str

    @property
    def repository(self) -> str:
        return f"{self.owner}/{self.repo}"

    def with_tag(self, tag: str) -> GitHubAssetRef:
        return GitHubAssetRef(owner=self.owner, repo=self.repo, tag=tag, asset=self.asset)

    def render(self) -> str:
        return f"github.com/{self.repository}@{self.tag}:{self.asset}"


def parse_github_ref(raw: str) -> GitHubAssetRef:
    match = _REF_RE.match(raw.strip())
    if not match:
        raise RefError(f"Invalid embedder ref: {raw}")
    asset = match["asset"]
    if "/" in asset or "\\" in asset:
        raise RefError(f"Release asset must be a basename: {asset}")
    return GitHubAssetRef(
        owner=match["owner"],
        repo=match["repo"],
        tag=match["tag"],
        asset=asset,
    )


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class GitHubProvider:
    def matches(self, raw: str) -> bool:
        return raw.startswith("github.com/")

    def parse_ref(self, raw: str) -> GitHubAssetRef:
        return parse_github_ref(raw)

    def resolve(self, ref: GitHubAssetRef) -> GitHubAssetRef:
        return ref.with_tag(self._latest_tag(ref))

    def resolve_cached(self, ref: GitHubAssetRef, cached: GitHubAssetRef) -> GitHubAssetRef:
        return ref.with_tag(cached.tag)

    def always_refresh(self, ref: GitHubAssetRef) -> bool:
        return False

    def fetch(self, ref: GitHubAssetRef, base_dir: Path) -> str:
        return self._download_asset(ref)

    def cache_key(self, ref: GitHubAssetRef) -> str:
        return ref.repository

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

    def _latest_tag(self, ref: GitHubAssetRef) -> str:
        result = self.run(
            ["release", "view", "--repo", ref.repository, "--json", "tagName", "--jq", ".tagName"]
        )
        if not result.stdout or result.stdout == "null":
            raise EmbedderError(f"Could not resolve latest release for {ref.repository}")
        return result.stdout

    def _download_asset(self, ref: GitHubAssetRef) -> str:
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
