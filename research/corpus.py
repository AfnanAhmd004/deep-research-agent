"""Load documents and split them into citable chunks (by heading, then by paragraph)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    id: str  # "doc#n"
    doc: str
    heading: str
    text: str

    @property
    def cite(self) -> str:
        return f"{self.doc} › {self.heading}" if self.heading else self.doc


CODE_LANGS = {"python", "py", "bash", "sh", "shell", "json", "yaml", "yml", "cpp", "c++", "c", "js", "javascript",
              "ts", "toml", "mermaid", "dockerfile", "sql"}


def _code_block(m: re.Match) -> str:
    """Keep console output (results!) as citable lines; drop source code and diagrams."""
    lang, body = m.group(1).strip().lower(), m.group(2)
    if lang in CODE_LANGS or body.count("\n") > 30:
        return ""
    keep = []
    for line in body.splitlines():
        line = line.strip()
        if not line or re.match(r"^(\$|pip |python |import |from |#|//|[{}\[\]])", line) or set(line) <= set("=-─┌┐└┘│▼ "):
            continue
        keep.append(line[:1].upper() + line[1:] + ("" if line.endswith(".") else "."))
    return "\n\n" + "\n".join(keep) + "\n\n"


def _clean(md: str) -> str:
    md = re.sub(r"```([^\n]*)\n(.*?)```", _code_block, md, flags=re.S)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)  # images
    md = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", md)  # links -> text
    md = re.sub(r"\*{1,3}|`", "", md)  # bold/italic/code markers (underscores kept: they appear in identifiers)
    return md


def chunk_markdown(doc: str, text: str, max_words: int = 110) -> list[Chunk]:
    chunks: list[Chunk] = []
    heading = ""
    buf: list[str] = []

    def flush() -> None:
        body = " ".join(" ".join(buf).split())
        buf.clear()
        if len(body.split()) < 6:
            return
        words = body.split()
        for i in range(0, len(words), max_words):
            piece = " ".join(words[max(0, i - 15): i + max_words])  # 15-word overlap between pieces
            chunks.append(Chunk(f"{doc}#{len(chunks)}", doc, heading, piece))

    header: list[str] | None = None
    for line in _clean(text).splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            flush()
            heading, header = m.group(2).strip(), None
            continue
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
                continue  # separator row
            if header is None:
                header = cells
                continue
            # a table row becomes a self-contained sentence: "row label: column value, column value."
            pairs = [f"{h} {v}".strip() for h, v in zip(header[1:], cells[1:]) if v]
            label = cells[0][:1].upper() + cells[0][1:]  # capitalised so each row is its own sentence
            buf.append(f"{label}: " + ", ".join(pairs) + ".")
            continue
        header = None
        if not line.strip():
            flush()
            continue
        buf.append(line.strip())
    flush()
    return chunks


def load_corpus(root: str | Path) -> list[Chunk]:
    out: list[Chunk] = []
    for p in sorted(Path(root).rglob("*")):
        if p.suffix.lower() in (".md", ".txt"):
            out.extend(chunk_markdown(p.stem, p.read_text(errors="ignore")))
    return out
