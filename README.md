# Embedder

Embedder is a dependency-style updater for embedded text fragments.

It is meant for shared instructions, policies, documentation fragments, and
other text blocks that must be materialized inside many repositories while still
having one upstream source of truth.

The core use case is agent instructions such as shared `AGENTS.md` sections:
the consuming repository keeps a local copy that agents can read without network
access, and Embedder periodically opens pull requests when the upstream fragment
changes.

## Model

Embedder treats a fragment embedded inside any text file as a dependency.

```text
consumer text file
  contains embedded block marker
    points to GitHub repository + release tag + release asset
      Embedder downloads latest fragment asset
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

- `github.com/OWNER/REPO` is the fragment source repository.
- `v0.3.0` is the currently pinned GitHub Release tag.
- `ASSET.md` is the release asset to embed. Asset names must be basenames, not
  nested paths.

The closing marker is always:

```markdown
<!-- /embedder -->
```

Everything between the markers is managed by Embedder and may be overwritten on
update. Everything outside the markers is local to the consuming repository.

## Releases

Fragment source repositories publish fragments as GitHub Release assets.

Assets do not need to be archives. A release may attach plain text files such as:

```text
agent-message-prefix.md
review-policy.md
security-guidance.md
fragments.yml
```

Embedder publishes its own introductory fragments:

```text
embedder-for-readmes.md
embedder-for-agents.md
```

These fragments explain managed blocks to people and coding agents. Consumers can
embed them in README or `AGENTS.md` files to make the source-repository workflow
explicit.

The source repository may store and build these assets however it wants. The
published release assets are the external contract consumed by Embedder.

Fragment source repositories can use the upload action to attach fragment assets
to a GitHub Release:

```yaml
- uses: rubykatzen/embedder/.github/actions/upload-fragments@v0
  with:
    release-tag: v1.2.3
    fragments-directory: fragments
```

`fragments-directory` defaults to `fragments`.

## Versioning

Embedder always updates to the latest GitHub Release.

GitHub prereleases are not considered latest releases by the MVP implementation.
Publish fragments as normal GitHub Releases when consumers should receive them.

SemVer tags such as `v0.3.0` are allowed for consistency with existing release
tooling, but Embedder does not implement major/minor/patch update strategies or
version constraints.

If a fragment needs fundamentally different behavior, publish it as a different
asset name instead of relying on compatibility semantics.

## Private Sources

Fragment sources may be public or private.

Public fragment assets can be downloaded without authentication. Private
fragment assets require a token with read access to the source repository.

This allows open source tooling in `rubykatzen/embedder` while keeping
organization-specific agent policies in private repositories.

## CLI

Install from the repository checkout:

```bash
pip install -e .
```

Commands:

```bash
embedder scan
embedder check
embedder update
embedder doctor
```

`embedder scan` finds all managed blocks in text files and prints their source,
release, asset, and containing file.

`embedder check` resolves each block against the latest source release and exits
non-zero when updates are available.

`embedder update` downloads the latest release asset for each managed block,
updates the marker tag, and replaces only the managed body.

`embedder doctor` checks local prerequisites such as GitHub CLI availability and
authentication.

All commands that inspect or change managed blocks accept optional file or
directory paths. When no path is provided, Embedder scans the current directory.

Use `--json` with `scan`, `check`, `update`, or `doctor` for machine-readable
output.

## GitHub Actions

Add this workflow to the consuming repository to check for fragment updates
daily and on demand:

```yaml
name: Update embedded fragments
on:
  schedule:
    - cron: "0 3 * * *"
  workflow_dispatch:

jobs:
  update:
    uses: rubykatzen/embedder/.github/workflows/update.yml@v0
```

When updates are available, Embedder opens a pull request:

```markdown
## Embedded fragment updates

| File | Source | Asset | Old | New |
|---|---|---|---:|---:|
| AGENTS.md | dupmachine/agent-guidelines | agent-message-prefix.md | v0.3.0 | v0.4.0 |
```

Repositories can rely on normal CI and automerge rules to land these PRs
automatically.

Pass `paths` to limit the scan to specific files or directories:

```yaml
jobs:
  update:
    uses: rubykatzen/embedder/.github/workflows/update.yml@v0
    with:
      paths: AGENTS.md docs/
```

Pass `token` to access fragments from private source repositories:

```yaml
jobs:
  update:
    uses: rubykatzen/embedder/.github/workflows/update.yml@v0
    secrets:
      token: ${{ secrets.FRAGMENT_SOURCE_TOKEN }}
```

## Release Process

Embedder releases are cut with the
[rubykatzen/releaser](https://github.com/rubykatzen/releaser) CLI. Run from
inside this repository:

```bash
releaser patch   # or: releaser minor / releaser major
```

The CLI verifies that CI is green on `origin/main`, calculates the next version,
dispatches `prepare-release.yml`, watches it run, then opens a `release/vX.Y.Z`
PR and enables auto-merge. `publish-release.yml` fires automatically once the PR
merges and creates the annotated tag, GitHub Release, and fragment release
assets using `.github/actions/upload-fragments`.

Check release readiness without triggering anything:

```bash
releaser status
releaser patch --dry-run
```

Install the CLI:

```bash
brew tap rubykatzen/tap && brew install releaser
```

## Design Constraints

- Works with arbitrary text files, not only Markdown.
- Owns only explicitly marked blocks.
- Uses GitHub Releases as the distribution mechanism.
- Downloads release assets directly; fragments do not need to be zipped.
- Supports public and private source repositories.
- Does not execute code from source repositories.
- Does not perform dependency solving or SemVer compatibility filtering.
- Keeps fragments materialized locally so agents can read them without network
  access.

## Status

The local CLI supports `scan`, `check`, `update`, and `doctor`. The reusable
GitHub Actions workflow is available at
`.github/workflows/update.yml`.
