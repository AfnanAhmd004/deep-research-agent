"""Hybrid retrieval: BM25 (exact terms) + character n-gram TF-IDF (fuzzy matches), fused with RRF.

Character n-grams catch morphology and spelling variants ("localisation" vs "localization",
"detectors" vs "detection") that word-level BM25 misses, without needing an embedding model.
"""
from __future__ import annotations

import math
import zlib
import re
from collections import Counter

import numpy as np

from .corpus import Chunk

STOP = set("a an and are as at be by for from has have how i in is it its of on or that the this to was were what "
           "when which who why with does do did vs versus than more most much many give gives get gets use uses used "
           "show shows per there their they can could would should about into between our your my me we us".split())


def _stem(t: str) -> str:
    for suf in ("ations", "ation", "ing", "ers", "er", "ed", "es", "s"):
        if len(t) > len(suf) + 3 and t.endswith(suf):
            return t[: -len(suf)]
    return t


def words(text: str) -> list[str]:
    """Lower-case, drop stop words, split hyphenated terms (keeping the whole), light suffix stemming."""
    out = []
    for w in re.findall(r"[a-z0-9][a-z0-9.\-^@]*[a-z0-9]|[a-z0-9]", text.lower()):
        if w in STOP:
            continue
        out.append(_stem(w))
        if "-" in w:
            out.extend(_stem(p) for p in w.split("-") if p and p not in STOP)
    return out


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.4, b: float = 0.7):
        self.tf = [Counter(words(d)) for d in docs]
        self.len = np.array([sum(t.values()) for t in self.tf], float)
        self.avg = float(self.len.mean())
        df = Counter(w for t in self.tf for w in t)
        n = len(docs)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}
        self.k1, self.b = k1, b

    def scores(self, query: str) -> np.ndarray:
        s = np.zeros(len(self.tf))
        for w in set(words(query)):
            if w not in self.idf:
                continue
            tf = np.array([t.get(w, 0) for t in self.tf], float)
            s += self.idf[w] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.len / self.avg))
        return s


class CharNgramTfidf:
    def __init__(self, docs: list[str], n: tuple[int, int] = (3, 5), dim: int = 2**18):
        self.n, self.dim = n, dim
        rows = [self._counts(d) for d in docs]
        df = Counter(h for r in rows for h in r)
        self.idf = {h: math.log((1 + len(docs)) / (1 + f)) + 1 for h, f in df.items()}
        self.vecs = [self._vec(r) for r in rows]

    def _counts(self, text: str) -> Counter:
        t = " " + " ".join(words(text)) + " "
        c: Counter = Counter()
        for k in range(self.n[0], self.n[1] + 1):
            for i in range(len(t) - k + 1):
                c[zlib.crc32(t[i:i + k].encode()) % self.dim] += 1  # stable across processes
        return c

    def _vec(self, counts: Counter) -> dict[int, float]:
        v = {h: (1 + math.log(c)) * self.idf.get(h, 1.0) for h, c in counts.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {h: x / norm for h, x in v.items()}

    def scores(self, query: str) -> np.ndarray:
        q = self._vec(self._counts(query))
        return np.array([sum(w * d.get(h, 0.0) for h, w in q.items()) for d in self.vecs])


class Retriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        texts = [f"{c.doc.replace('-', ' ')} {c.heading} {c.text}" for c in chunks]
        self.bm25 = BM25(texts)
        self.char = CharNgramTfidf(texts)

    def search(self, query: str, k: int = 5, mode: str = "hybrid", rrf_k: int = 60) -> list[tuple[Chunk, float]]:
        if mode == "bm25":
            s = self.bm25.scores(query)
        elif mode == "char":
            s = self.char.scores(query)
        else:  # reciprocal rank fusion (Cormack et al., 2009)
            s = np.zeros(len(self.chunks))
            for scores in (self.bm25.scores(query), self.char.scores(query)):
                ranks = np.empty(len(scores), int)
                ranks[np.argsort(-scores)] = np.arange(len(scores))
                s += 1.0 / (rrf_k + ranks + 1)
        top = np.argsort(-s)[:k]
        return [(self.chunks[i], float(s[i])) for i in top]

    def coverage(self, query: str, k: int = 5) -> float:
        """IDF-weighted share of the query's terms found in the top-k BM25 chunks.

        Low coverage means the corpus does not discuss the question: abstain instead of
        answering from loosely related text. Unknown terms count with the maximum IDF.
        """
        q = set(words(query))
        if not q:
            return 0.0
        top = np.argsort(-self.bm25.scores(query))[:k]
        present = set().union(*(self.bm25.tf[i].keys() for i in top))
        max_idf = max(self.bm25.idf.values())
        w = {t: self.bm25.idf.get(t, max_idf) for t in q}
        return sum(v for t, v in w.items() if t in present) / sum(w.values())

    def idf(self, term: str) -> float:
        return self.bm25.idf.get(term, max(self.bm25.idf.values()))
