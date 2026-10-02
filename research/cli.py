"""deep-research "your question" --corpus path/to/docs [--model <claude-model-id>]"""
from __future__ import annotations

import argparse

from .agent import ResearchAgent, anthropic_writer
from .corpus import load_corpus
from .retrieve import Retriever


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="deep-research")
    ap.add_argument("question")
    ap.add_argument("--corpus", default="corpus")
    ap.add_argument("--model", help="use Claude as the writer (needs ANTHROPIC_API_KEY)")
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args(argv)
    r = Retriever(load_corpus(args.corpus))
    agent = ResearchAgent(r, writer=anthropic_writer(args.model) if args.model else None, k=args.k)
    print(agent.run(args.question).markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
