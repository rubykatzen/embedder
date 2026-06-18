import pytest

from embedder.refs import RefError, parse_ref


def test_parse_ref() -> None:
    ref = parse_ref("github.com/OWNER/repo-name@v0.3.0:agent-message-prefix.md")

    assert ref.owner == "OWNER"
    assert ref.repo == "repo-name"
    assert ref.tag == "v0.3.0"
    assert ref.asset == "agent-message-prefix.md"
    assert ref.repository == "OWNER/repo-name"
    assert ref.render() == "github.com/OWNER/repo-name@v0.3.0:agent-message-prefix.md"


def test_ref_with_new_tag() -> None:
    ref = parse_ref("github.com/rubykatzen/embedder@v0.1.0:snippet.md")

    assert ref.with_tag("v0.2.0").render() == "github.com/rubykatzen/embedder@v0.2.0:snippet.md"


def test_reject_invalid_ref() -> None:
    with pytest.raises(RefError):
        parse_ref("rubykatzen/embedder@v0.1.0:snippet.md")
