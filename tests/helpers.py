def marker(ref: str) -> str:
    return "<!-- " + f"embedder {ref} -->"


def close_marker() -> str:
    return "<!-- " + "/embedder -->"


def yaml_marker(ref: str) -> str:
    return f"# embedder {ref}"


def yaml_close_marker() -> str:
    return "# /embedder"
