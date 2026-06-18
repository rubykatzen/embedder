## Embedded Fragments

This repository uses [Embedder](https://github.com/rubykatzen/embedder) to keep
shared documentation fragments synchronized across repositories.

Content between `<!-- embedder ... -->` and `<!-- /embedder -->` markers is
managed. Local changes inside those markers may be overwritten by the next
Embedder update.

To change an embedded fragment, open a pull request in the source repository
named in the opening marker, not in the consuming repository. The source
repository publishes fragment updates as GitHub Release assets, and consuming
repositories receive those updates through normal dependency-style pull requests.
