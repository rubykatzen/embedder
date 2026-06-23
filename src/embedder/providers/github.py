from __future__ import annotations

import base64
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from embedder.errors import EmbedderEnvironmentError, EmbedderError, RefError

_REF_RE = re.compile(
    r"^github\.com/"
    r"(?P<owner>[A-Za-z0-9_.-]+)/"
    r"(?P<repo>[A-Za-z0-9_.-]+)"
    r"(?:@(?P<tag>[^:\s]+))?"
    r":(?P<asset>[^\s]+)$"
)

_SEMVER_RE = re.compile(r"^v?\d+(\.\d+)*$")


@dataclass(frozen=True)
class GitHubAssetRef:
    owner: str
    repo: str
    asset: str
    tag: str | None = None

    @property
    def repository(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def is_pinned(self) -> bool:
        return self.tag is not None and bool(_SEMVER_RE.match(self.tag))

    def with_tag(self, tag: str) -> GitHubAssetRef:
        return GitHubAssetRef(owner=self.owner, repo=self.repo, asset=self.asset, tag=tag)

    def render(self) -> str:
        if self.tag is None:
            return f"github.com/{self.repository}:{self.asset}"
        return f"github.com/{self.repository}@{self.tag}:{self.asset}"


def parse_github_ref(raw: str) -> GitHubAssetRef:
    match = _REF_RE.match(raw.strip())
    if not match:
        raise RefError(f"Invalid embedder ref: {raw}")
    asset = match["asset"]
    parts = asset.split("/")
    if asset.startswith("/") or ".." in parts or "." in parts:
        raise RefError(
            f"Asset path must be a relative path without '.' or '..' segments: {asset!r}"
        )
    return GitHubAssetRef(
        owner=match["owner"],
        repo=match["repo"],
        asset=asset,
        tag=match.group("tag"),
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
        # Validate gh is available for any GitHub ref, then return as-is.
        # Tagless and branch refs are handled via always_refresh + fetch.
        self.require()
        return ref

    def always_refresh(self, ref: GitHubAssetRef) -> bool:
        return not ref.is_pinned

    def fetch(self, ref: GitHubAssetRef, base_dir: Path) -> str:
        return self._fetch_file(ref)

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
            ["api", f"repos/{ref.repository}/releases/latest", "--jq", ".tag_name"]
        )
        if not result.stdout or result.stdout == "null":
            raise EmbedderError(f"Could not resolve latest release for {ref.repository}")
        return result.stdout

    def _fetch_file(self, ref: GitHubAssetRef) -> str:
        tag = ref.tag if ref.tag is not None else self._latest_tag(ref)
        encoded_asset = quote(ref.asset, safe="/")
        encoded_tag = quote(tag, safe="")
        result = self.run(
            [
                "api",
                f"repos/{ref.repository}/contents/{encoded_asset}?ref={encoded_tag}",
                "--jq",
                ".content",
            ]
        )
        if not result.stdout or result.stdout == "null":
            raise EmbedderError(
                f"File not found or not a regular file: {ref.render()!r}"
            )
        return base64.b64decode(result.stdout).decode("utf-8")
