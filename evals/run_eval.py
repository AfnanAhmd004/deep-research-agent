"""Evaluate retrieval, answers, citations and abstention on evals/questions.jsonl.

    python evals/run_eval.py
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from research import Claim, ResearchAgent, Retriever, load_corpus, verify_claim  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = [json.loads(l) for l in (ROOT / "evals" / "questions.jsonl").read_text().splitlines()]


def retrieval_table(r: Retriever) -> None:
    print("=== retrieval: gold document in top-k (answerable questions) ===")
    print(f"{'mode':<8}{'recall@1':>10}{'recall@5':>10}")
    ans = [q for q in QUESTIONS if q["answerable"]]
    for mode in ("bm25", "char", "hybrid"):
        r1 = sum(r.search(q["question"], 1, mode)[0][0].doc == q["gold_doc"] for q in ans) / len(ans)
        r5 = sum(q["gold_doc"] in {c.doc for c, _ in r.search(q["question"], 5, mode)} for q in ans) / len(ans)
        print(f"{mode:<8}{r1:>10.0%}{r5:>10.0%}")


def answer_table(agent: ResearchAgent) -> None:
    ans = [q for q in QUESTIONS if q["answerable"]]
    unans = [q for q in QUESTIONS if not q["answerable"]]
    fact_hits, abstain_wrong, claims, supported, cited_gold = 0, 0, 0, 0, 0
    misses = []
    for q in ans:
        rep = agent.run(q["question"])
        text = " ".join(c.text for c in rep.claims)
        hit = any(f in text for f in q["gold_facts"])
        fact_hits += hit
        abstain_wrong += rep.abstained
        claims += len(rep.claims)
        supported += sum(c.supported for c in rep.claims)
        cited_gold += any(rep.sources[x].doc == q["gold_doc"] for c in rep.claims for x in c.citations)
        if not hit:
            misses.append(q["question"])
    abstained = sum(agent.run(q["question"]).abstained for q in unans)
    print("\n=== answers (extractive writer, offline) ===")
    print(f"answer contains a gold fact      {fact_hits}/{len(ans)} ({fact_hits / len(ans):.0%})")
    print(f"cites the gold document          {cited_gold}/{len(ans)}")
    print(f"claims supported by their source {supported}/{claims}")
    print(f"wrongly abstained (answerable)   {abstain_wrong}/{len(ans)}")
    print(f"correctly abstained (off-topic)  {abstained}/{len(unans)}")
    if misses:
        print("missed:", *[f"  - {m}" for m in misses], sep="\n")


def verifier_table(agent: ResearchAgent) -> None:
    """Simulate a sloppy writer: corrupt numbers or swap in unrelated sentences, count what verification catches."""
    rng = random.Random(0)
    ok_claims, bad_claims = [], []
    for q in [q for q in QUESTIONS if q["answerable"]]:
        rep = agent.run(q["question"])
        for c in rep.claims:
            src = " ".join(rep.sources[x].text for x in c.citations)
            ok_claims.append((c.text, src))
            # corrupt one standalone figure (not digits inside identifiers like agent_v2 or n8n)
            spans = [m for m in re.finditer(r"(?<![\w.])\d+(?:\.\d+)?(?![\w])", c.text)]
            if spans:
                m = rng.choice(spans)
                n = m.group(0)
                wrong = str(round(float(n) * rng.choice([0.5, 1.5, 2, 10]) + 1, 2)).rstrip("0").rstrip(".")
                bad_claims.append(("number", c.text[:m.start()] + wrong + c.text[m.end():], src))
    other = [s for _, s in ok_claims]
    for text, src in ok_claims[:40]:
        bad_claims.append(("wrong source", text, rng.choice([o for o in other if o != src])))
    kept_ok = sum(verify_claim(t, s).supported for t, s in ok_claims)
    print("\n=== claim verification ===")
    print(f"correct claims kept               {kept_ok}/{len(ok_claims)}")
    for kind in ("number", "wrong source"):
        rows = [(t, s) for k, t, s in bad_claims if k == kind]
        caught = sum(not verify_claim(t, s).supported for t, s in rows)
        print(f"corrupted ({kind:<12}) caught {caught}/{len(rows)} ({caught / max(len(rows), 1):.0%})")


def main() -> None:
    chunks = load_corpus(ROOT / "corpus")
    r = Retriever(chunks)
    print(f"corpus: {len({c.doc for c in chunks})} documents, {len(chunks)} chunks\n")
    retrieval_table(r)
    agent = ResearchAgent(r)
    answer_table(agent)
    verifier_table(agent)


if __name__ == "__main__":
    main()
