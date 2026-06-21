from __future__ import annotations


class EmbedderError(Exception):
    pass


class EmbedderEnvironmentError(EmbedderError):
    pass


class RefError(ValueError):
    pass
