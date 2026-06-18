from __future__ import annotations

import re
from dataclasses import dataclass


REF_RE = re.compile(
    r"^github\.com/"
    r"(?P<owner>[A-Za-z0-9_.-]+)/"
    r"(?P<repo>[A-Za-z0-9_.-]+)"
    r"@(?P<tag>[^:\s]+)"
    r":(?P<asset>[^\s]+)$"
)


class RefError(ValueError):
    pass


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
        return GitHubAssetRef(
            owner=self.owner,
            repo=self.repo,
            tag=tag,
            asset=self.asset,
        )

    def render(self) -> str:
        return f"github.com/{self.repository}@{self.tag}:{self.asset}"


def parse_ref(raw: str) -> GitHubAssetRef:
    match = REF_RE.match(raw.strip())
    if not match:
        raise RefError(f"Invalid embedder ref: {raw}")
    return GitHubAssetRef(
        owner=match["owner"],
        repo=match["repo"],
        tag=match["tag"],
        asset=match["asset"],
    )
