"""Check that each claim is supported by the passage it cites.

Two cheap, transparent tests catch most citation errors without a model:

1. **Numbers**: every number in the claim must appear in the cited passage
   (the most common and most damaging hallucination in technical answers).
2. **Content overlap**: most of the claim's content words must appear in the passage.

An optional model judge can be layered on top for paraphrased claims.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .retrieve import words

NUM = re.compile(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)*(?:\.\d+)?")


def numbers(text: str) -> set[str]:
    out = set()
    for m in NUM.findall(text):
        n = m.replace(",", "").lstrip("+")
        try:
            v = float(n)
        except ValueError:
            continue
        out.add(f"{v:g}")
    return out


@dataclass
class Verdict:
    supported: bool
    reason: str
    overlap: float


def verify_claim(claim: str, passage: str, min_overlap: float = 0.6) -> Verdict:
    missing = numbers(claim) - numbers(passage)
    if missing:
        return Verdict(False, f"numbers not in source: {', '.join(sorted(missing))}", 0.0)
    cw = set(words(claim))
    if not cw:
        return Verdict(False, "empty claim", 0.0)
    pw = set(words(passage))
    overlap = len(cw & pw) / len(cw)
    if overlap < min_overlap:
        return Verdict(False, f"only {overlap:.0%} of the claim's words are in the source", overlap)
    return Verdict(True, "supported", overlap)
