<!-- pyml disable-next-line MD041 -->
## Embedded Fragment Policy

This repository uses [Embedder](https://github.com/rubykatzen/embedder) to keep
shared documentation fragments synchronized across repositories.

Do not edit content inside `<!-- embedder ... -->` and `<!-- /embedder -->`
markers directly. Embedder owns the managed block body and may overwrite local
changes during the next update.

If a managed fragment needs to change, open a pull request in the source
repository referenced by the opening marker. Only edit the consuming repository
when changing text outside managed markers or when intentionally changing the
marker source, release tag, or asset name.
