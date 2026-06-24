# Changelog

## [Unreleased]

## [v0.2.2] - 2026-06-24

- Update dependabot.yml
- chore: change dependabot schedule time to 10:00 Berlin
- chore: add all ecosystems to dependabot fragment
- chore: update dependabot fragment to common config (daily, Berlin timezone)

## [v0.2.1] - 2026-06-24

- refactor: pass paths directly instead of through env vars
- chore: bump embedder actions to v0.2 in update-fragments-shared
- chore: use install-embedder action in prepare-release
- chore: bump install-embedder to v0.2

## [v0.2.0] - 2026-06-23

- fix: update dependabot.yml marker to ./ local ref format
- fix: install embedder from local source in prepare-release
- fix: enable install-embedder and push-release-branch steps
- fix: sort imports in test_updater.py (#32)
- chore: comment out release steps pending fix
- chore: remove bump-shared-workflow-version action
- Update prepare-release.yml
- chore: pin install-embedder to v0.1
- refactor: normalize action composition for embedder install
- chore: update embedded fragments (#22)
- chore: switch to baseline lint-shared workflow v0.7 (#31)
- feat: support git refs and file paths via GitHub contents API (#30)

## [v0.1.3] - 2026-06-22

- fix: use explicit repo ref for open-fragments-pr in shared workflow

## [v0.1.2] - 2026-06-22

- fix: bump install-embedder reference to v0.1 in shared workflow

## [v0.1.1] - 2026-06-22

- chore: pin releaser actions to minor versions instead of patch (#21)

## [v0.1.0] - 2026-06-21

- fix: remove invalid workflows permission, disable bump-shared-workflow-version step
- fix: suppress actionlint false positive for workflows permission scope
- fix: add workflows permission for bump-shared-workflow-version step
- chore(deps): bump rubykatzen/releaser from 0.3.4 to 0.5.0 (#15)
- feat: extensible format and provider system (#14)

## [v0.0.6] - 2026-06-21

- fix: trigger Homebrew tap update without workflow inputs (#10)

## [v0.0.5] - 2026-06-21

- fix: install embedder from pinned release
- fix: install embedder from explicit workflow ref

## [v0.0.4] - 2026-06-20

- feat: add GitHub Copilot to message-prefix agent list
- chore: bump baseline to v0.6.2, remove MD022 workaround blank lines
- fix: add blank line after embedder marker to satisfy MD022
- feat: add message-prefix fragment and embed in AGENTS.md

## [v0.0.3] - 2026-06-20

- fix: remove blank lines to pass yamllint
- chore: rename to update-fragments-shared.yml
- chore: rename update.yml to update-fragments.yml
- fix: use GITHUB_WORKFLOW_SHA and env var for paths input
- feat: add reusable update workflow for consumers

## [v0.0.2] - 2026-06-19

- docs: document releaser workflow
- Update embedder-for-readmes.md
- chore: bump baseline to v0.5.2
- ci: add upload fragments action
- feat: add introductory fragments
- docs: adopt fragment terminology

## [v0.0.1] - 2026-06-18

- [codex] add embedder CLI MVP (#1)
- docs: update claude code emoji
- docs: add agent instructions
- docs: add embedder design draft
