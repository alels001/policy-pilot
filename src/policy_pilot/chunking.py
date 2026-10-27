"""Split a Markdown document into chunks, one per section (## heading)."""

from dataclasses import dataclass

MAX_CHARS = 1200
DOCUMENT_INFO = "Document info"


@dataclass(frozen=True)
class Chunk:
    section: str
    text: str


def split_markdown(markdown: str) -> list[Chunk]:
    sections: list[tuple[str, list[str]]] = []
    heading = DOCUMENT_INFO
    lines: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            sections.append((heading, lines))
            heading = line[3:].strip()
            lines = []
        else:
            lines.append(line)
    sections.append((heading, lines))

    chunks = []
    for heading, lines in sections:
        text = "\n".join(lines).strip()
        if text:
            chunks.extend(Chunk(heading, part) for part in _split_long(text))
    return chunks


def _split_long(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Very long sections are split at paragraph boundaries, never in the middle of a sentence."""
    if len(text) <= max_chars:
        return [text]

    parts: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        if current and len(current) + len(paragraph) + 2 > max_chars:
            parts.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        parts.append(current)
    return parts
