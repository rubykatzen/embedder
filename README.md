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
    points to GitHub repository + ref + file path
      Embedder fetches the file at that ref via the GitHub contents API
        replaces only the managed block body
          opens a pull request
```

This is intentionally not a project template manager. Embedder owns only the
marked blocks, not the surrounding file.

## Block Format

Managed blocks use one-line markers:

```markdown
<!-- embedder github.com/OWNER/REPO@v0.3.0:path/to/file.md -->
managed text goes here
<!-- /embedder -->
```

The closing marker is always `<!-- /embedder -->`. Everything between the
markers is managed by Embedder. Everything outside is local to the consuming
repository.

### Ref modes

**Auto-latest** — omit the tag to always track the latest release. The marker
stays tagless; no version is written back, so there are no circular update
loops:

```markdown
<!-- embedder github.com/OWNER/REPO:path/to/file.md -->
```

**Pinned** — include a semver tag to freeze the content at a specific release.
Embedder never bumps a pinned marker automatically:

```markdown
<!-- embedder github.com/OWNER/REPO@v0.3.0:path/to/file.md -->
```

**Branch** — include a non-semver ref to track a branch or commit. Content is
re-fetched on every update run; the marker ref is never changed:

```markdown
<!-- embedder github.com/OWNER/REPO@main:path/to/file.md -->
```

### File paths

The file path is relative to the repository root and may include subdirectories:

```markdown
<!-- embedder github.com/OWNER/REPO@v0.3.0:docs/fragments/policy.md -->
```

## Fragment Sources

Embedder fetches files directly from a GitHub repository's file tree using the
GitHub contents API. Any file committed at the target ref is a valid fragment
source — no need to attach files as release assets.

Embedder publishes its own introductory fragments under the `fragments/`
directory:

```text
fragments/embedder-for-readmes.md
fragments/embedder-for-agents.md
```

These explain managed blocks to people and coding agents. Consumers can embed
them in README or `AGENTS.md` files to make the source-repository workflow
explicit.

## Versioning

Auto-latest markers resolve to the latest GitHub Release. GitHub prereleases are
not considered latest releases. Publish normal releases when consumers should
receive updates.

Embedder does not implement major/minor/patch update strategies or version
constraints. If a fragment needs fundamentally different behavior, publish it
under a different file path instead of relying on compatibility semantics.

## Private Sources

Fragment sources may be public or private.

Public fragment sources can be fetched without authentication. Private
repositories require a token with read access to the source repository.

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

`embedder scan` finds all managed blocks in text files and prints their source
repository, ref, file path, and containing file.

`embedder check` resolves each block against the latest source release and exits
non-zero when updates are available.

`embedder update` fetches the current file for each managed block and replaces
only the managed body. The marker ref is preserved as-is; pinned tags are never
bumped automatically.

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
    uses: rubykatzen/embedder/.github/workflows/update-fragments-shared.yml@v0
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
    uses: rubykatzen/embedder/.github/workflows/update-fragments-shared.yml@v0
    with:
      paths: AGENTS.md docs/
```

Pass `token` to access fragments from private source repositories:

```yaml
jobs:
  update:
    uses: rubykatzen/embedder/.github/workflows/update-fragments-shared.yml@v0
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
- Fetches files via the GitHub contents API; any file in the repo tree is a
  valid fragment source.
- Supports public and private source repositories.
- Does not execute code from source repositories.
- Does not perform dependency solving or SemVer compatibility filtering.
- Keeps fragments materialized locally so agents can read them without network
  access.

## Status

The local CLI supports `scan`, `check`, `update`, and `doctor`. The reusable
GitHub Actions workflow is available at
`.github/workflows/update-fragments-shared.yml`.
