"""The research loop: plan → retrieve → read → write with citations → verify → report."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Callable, Protocol

from .corpus import Chunk
from .retrieve import Retriever, words
from .verify import numbers, verify_claim


@dataclass
class Claim:
    text: str
    citations: list[str]  # chunk ids
    supported: bool = False
    reason: str = ""


@dataclass
class Report:
    question: str
    subquestions: list[str]
    claims: list[Claim]
    sources: dict[str, Chunk]
    unanswered: list[str] = field(default_factory=list)
    dropped: list[Claim] = field(default_factory=list)

    @property
    def abstained(self) -> bool:
        return not self.claims

    def markdown(self) -> str:
        order = []
        for c in self.claims:
            for cid in c.citations:
                if cid not in order:
                    order.append(cid)
        num = {cid: i + 1 for i, cid in enumerate(order)}
        lines = [f"## {self.question}", ""]
        if self.abstained:
            lines.append("_The documents do not contain enough information to answer this._")
        for c in self.claims:
            lines.append(f"- {c.text} " + "".join(f"[{num[x]}]" for x in c.citations))
        if self.unanswered:
            lines += ["", "**Not found in the documents:** " + "; ".join(self.unanswered)]
        if self.dropped:
            lines += ["", f"_{len(self.dropped)} claim(s) removed by verification._"]
        if order:
            lines += ["", "**Sources**"] + [f"{num[c]}. {self.sources[c].cite}" for c in order]
        return "\n".join(lines)


# ------------------------------------------------------------------------- planner -------
def plan_heuristic(question: str) -> list[str]:
    """Split compound questions; keep the full question as the first sub-query."""
    q = question.strip().rstrip("?")
    parts = [p.strip() for p in re.split(r"\?|;|\band also\b|\. |,?\s+and\s+(?=(?:what|how|which|who|when|where|why|"
                                         r"is|are|does|do)\b)", q, flags=re.I) if len(p.split()) >= 3]
    m = re.match(r"(?i)(?:compare|how does|how do)\s+(.+?)\s+(?:and|vs\.?|versus|compare to|compared to)\s+(.+)", q)
    if m:
        parts += [m.group(1), m.group(2)]
    out = [q] + [p for p in parts if p.lower() != q.lower()]
    return list(dict.fromkeys(out))[:4]


# ------------------------------------------------------------------------- writer --------
_SENT = re.compile(r"(?<=[.!?;])\s+(?=[A-Z0-9*(])")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(text) if len(s.split()) >= 5]


def write_extractive(question: str, sub: str, hits: list[tuple[Chunk, float]], max_claims: int = 2,
                     idf: Callable[[str], float] | None = None) -> list[Claim]:
    """Pick the passage sentences that best answer the sub-question (no model needed).

    Sentences are scored by the IDF-weighted share of the question's terms they contain,
    with a bonus for numbers when the question asks for a quantity.
    """
    idf = idf or (lambda t: 1.0)
    qw = set(words(sub))  # score against the focused sub-question, not the whole compound question
    total = sum(idf(t) for t in qw) or 1.0
    wants_number = bool(re.search(r"(?i)\b(how (much|many|fast|early|earlier)|what (is|was|are) the|by how|rate|"
                                  r"accuracy|percent|%|delay|cost|latency)", question + " " + sub))
    scored = []
    for rank, (ch, _) in enumerate(hits):
        context = set(words(ch.heading)) | set(words(ch.doc.replace("-", " ")))
        for s in _sentences(ch.text):
            if len(s.split()) > 60:
                continue
            sw = set(words(s)) | context
            score = sum(idf(t) for t in qw & sw) / total - 0.03 * rank + (0.15 if wants_number and numbers(s) else 0)
            scored.append((score, s, ch.id))
    scored.sort(key=lambda x: -x[0])
    claims, seen = [], set()
    for score, s, cid in scored:
        if score < 0.35 or s[:60] in seen:
            continue
        seen.add(s[:60])
        claims.append(Claim(s, [cid]))
        if len(claims) == max_claims:
            break
    return claims


class Writer(Protocol):
    def __call__(self, question: str, sub: str, hits: list[tuple[Chunk, float]]) -> list[Claim]: ...


def anthropic_writer(model: str) -> Writer:
    """Claude writes claims as JSON with chunk-id citations (``pip install anthropic``)."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def write(question: str, sub: str, hits):
        passages = "\n\n".join(f"[{c.id}] ({c.cite}) {c.text}" for c, _ in hits)
        prompt = (f"Question: {question}\nFocus: {sub}\n\nPassages:\n{passages}\n\n"
                  "Answer using ONLY the passages. Return JSON: [{\"claim\": str, \"cite\": [passage ids]}]. "
                  "Copy numbers exactly. If the passages do not answer, return [].")
        r = client.messages.create(model=model, max_tokens=800, messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in r.content if b.type == "text")
        try:
            data = json.loads(text[text.index("["): text.rindex("]") + 1])
        except ValueError:
            return []
        return [Claim(str(d.get("claim", "")), [str(x) for x in d.get("cite", [])]) for d in data if d.get("claim")]

    return write


# ------------------------------------------------------------------------- agent ---------
class ResearchAgent:
    def __init__(self, retriever: Retriever, writer: Writer | None = None,
                 planner: Callable[[str], list[str]] = plan_heuristic, k: int = 5, min_coverage: float = 0.55,
                 verify: bool = True):
        self.r, self.planner, self.k = retriever, planner, k
        self.writer = writer or (lambda q, sub, hits: write_extractive(q, sub, hits, idf=retriever.idf))
        self.min_coverage, self.verify = min_coverage, verify

    def run(self, question: str) -> Report:
        subs = self.planner(question)
        sources: dict[str, Chunk] = {}
        claims: list[Claim] = []
        unanswered = []
        for sub in subs:
            if self.r.coverage(sub) < self.min_coverage:  # corpus does not cover this: say so, do not guess
                unanswered.append(sub)
                continue
            hits = self.r.search(sub, k=self.k)
            for c, _ in hits:
                sources[c.id] = c
            new = self.writer(question, sub, hits)
            if not new:
                unanswered.append(sub)
            claims += [c for c in new if c.text not in {x.text for x in claims}]
        kept, dropped = [], []
        for c in claims:
            cited = [sources[x] for x in c.citations if x in sources]
            if not cited:
                c.supported, c.reason = False, "cites a passage that was not retrieved"
            else:
                v = verify_claim(c.text, " ".join(ch.text for ch in cited))
                c.supported, c.reason = v.supported, v.reason
            (kept if (c.supported or not self.verify) else dropped).append(c)
        if subs and subs[0] in unanswered:  # the main question itself is not covered
            kept = []
        return Report(question, subs, kept, sources, unanswered, dropped)
