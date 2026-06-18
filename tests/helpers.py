def marker(ref: str) -> str:
    return "<!-- " + f"embedder {ref} -->"


def close_marker() -> str:
    return "<!-- " + "/embedder -->"
