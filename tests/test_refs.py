import pytest

from embedder.errors import RefError
from embedder.providers import parse_ref
from embedder.providers.github import GitHubAssetRef, parse_github_ref
from embedder.providers.local import LocalRef


def test_parse_github_ref() -> None:
    ref = parse_github_ref("github.com/OWNER/repo-name@v0.3.0:agent-message-prefix.md")

    assert ref.owner == "OWNER"
    assert ref.repo == "repo-name"
    assert ref.tag == "v0.3.0"
    assert ref.asset == "agent-message-prefix.md"
    assert ref.repository == "OWNER/repo-name"
    assert ref.render() == "github.com/OWNER/repo-name:agent-message-prefix.md"


def test_parse_github_ref_without_version() -> None:
    ref = parse_github_ref("github.com/OWNER/repo-name:agent-message-prefix.md")

    assert ref.owner == "OWNER"
    assert ref.repo == "repo-name"
    assert ref.tag is None
    assert ref.asset == "agent-message-prefix.md"
    assert ref.render() == "github.com/OWNER/repo-name:agent-message-prefix.md"


def test_github_ref_with_new_tag() -> None:
    ref = parse_github_ref("github.com/rubykatzen/embedder@v0.1.0:fragment.md")

    assert ref.with_tag("v0.2.0").render() == "github.com/rubykatzen/embedder:fragment.md"


def test_reject_invalid_github_ref() -> None:
    with pytest.raises(RefError):
        parse_github_ref("rubykatzen/embedder@v0.1.0:fragment.md")


def test_reject_nested_asset_path() -> None:
    with pytest.raises(RefError, match="basename"):
        parse_github_ref("github.com/rubykatzen/embedder@v0.1.0:fragments/fragment.md")


def test_parse_ref_dispatches_github() -> None:
    ref = parse_ref("github.com/rubykatzen/embedder@v0.1.0:fragment.md")

    assert isinstance(ref, GitHubAssetRef)


def test_parse_ref_dispatches_local() -> None:
    ref = parse_ref("local:fragments/file.md")

    assert isinstance(ref, LocalRef)
    assert ref.path == "fragments/file.md"
    assert ref.render() == "local:fragments/file.md"


def test_parse_ref_rejects_unknown_scheme() -> None:
    with pytest.raises(RefError, match="Unknown ref scheme"):
        parse_ref("s3://bucket/file.md")
