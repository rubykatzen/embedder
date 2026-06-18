# Embedder

Embedder is a dependency-style updater for embedded text snippets.

It is meant for shared instructions, policies, documentation fragments, and
other text blocks that must be materialized inside many repositories while still
having one upstream source of truth.

The core use case is agent instructions such as shared `AGENTS.md` sections:
the consuming repository keeps a local copy that agents can read without network
access, and Embedder periodically opens pull requests when the upstream snippet
changes.

## Model

Embedder treats a managed block inside any text file as a dependency.

```text
consumer text file
  contains embedded block marker
    points to GitHub repository + release tag + release asset
      Embedder downloads latest release asset
        replaces only the managed block body
          opens a pull request
```

This is intentionally not a project template manager. Embedder owns only the
marked blocks, not the surrounding file.

## Block Format

Managed blocks use one-line markers:

```markdown
<!-- embedder github.com/OWNER/REPO@v0.3.0:ASSET.md -->
managed text goes here
<!-- /embedder -->
```

Example:

```markdown
<!-- embedder github.com/dupmachine/agent-guidelines@v0.3.0:agent-message-prefix.md -->
## Message Prefix

Prefix every user-visible agent message with the agent emoji followed by the
repository name in square brackets:

`EMOJI [OWNER/REPO]:`
<!-- /embedder -->
```

The marker means:

- `github.com/OWNER/REPO` is the snippet source repository.
- `v0.3.0` is the currently pinned GitHub Release tag.
- `ASSET.md` is the release asset to embed.

The closing marker is always:

```markdown
<!-- /embedder -->
```

Everything between the markers is managed by Embedder and may be overwritten on
update. Everything outside the markers is local to the consuming repository.

## Releases

Snippet source repositories publish snippets as GitHub Release assets.

Assets do not need to be archives. A release may attach plain text files such as:

```text
agent-message-prefix.md
review-policy.md
security-guidance.md
snippets.yml
```

The source repository may store and build these assets however it wants. The
published release assets are the external contract consumed by Embedder.

## Versioning

Embedder always updates to the latest GitHub Release.

SemVer tags such as `v0.3.0` are allowed for consistency with existing release
tooling, but Embedder does not implement major/minor/patch update strategies or
version constraints.

If a snippet needs fundamentally different behavior, publish it as a different
asset name instead of relying on compatibility semantics.

## Private Sources

Snippet sources may be public or private.

Public source assets can be downloaded without authentication. Private source
assets require a token with read access to the source repository.

This allows open source tooling in `rubykatzen/embedder` while keeping
organization-specific agent policies in private repositories.

## CLI

Planned commands:

```bash
embedder scan
embedder check
embedder update
```

`embedder scan` finds all managed blocks in text files and prints their source,
release, asset, and containing file.

`embedder check` resolves each block against the latest source release and exits
non-zero when updates are available.

`embedder update` downloads the latest release asset for each managed block,
updates the marker tag, and replaces only the managed body.

## GitHub Actions

Embedder should provide a reusable workflow for consumers:

```yaml
name: Update embedded snippets
on:
  schedule:
    - cron: "0 3 * * *"
  workflow_dispatch:

jobs:
  update:
    uses: rubykatzen/embedder/.github/workflows/update.yml@v1
    secrets: inherit
```

The workflow should:

1. Check out the consuming repository.
2. Install or run the Embedder CLI.
3. Run `embedder update`.
4. Open a pull request if any managed blocks changed.

Pull requests should look like dependency update PRs:

```markdown
## Embedded snippet updates

| File | Source | Asset | Old | New |
|---|---|---|---:|---:|
| AGENTS.md | dupmachine/agent-guidelines | agent-message-prefix.md | v0.3.0 | v0.4.0 |
```

Repositories can then rely on normal CI and automerge rules.

## Design Constraints

- Works with arbitrary text files, not only Markdown.
- Owns only explicitly marked blocks.
- Uses GitHub Releases as the distribution mechanism.
- Downloads release assets directly; snippets do not need to be zipped.
- Supports public and private source repositories.
- Does not execute code from source repositories.
- Does not perform dependency solving or SemVer compatibility filtering.
- Keeps snippets materialized locally so agents can read them without network
  access.

## Status

Design draft. No implementation yet.
