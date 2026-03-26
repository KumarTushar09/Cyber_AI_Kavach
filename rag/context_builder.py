def build_context(chunks: list[dict]) -> str:
    lines: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        source = chunk.get("source", "unknown")
        score = float(chunk.get("similarity", 0.0))
        text = chunk.get("text", "")
        lines.append(f"[{index}] source={source} similarity={score:.4f}")
        lines.append(text)
    return "\n\n".join(lines)
