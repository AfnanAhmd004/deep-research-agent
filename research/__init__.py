"""deep-research-agent: cited, verified answers from your own documents."""
from .agent import Claim, Report, ResearchAgent, anthropic_writer, plan_heuristic, write_extractive
from .corpus import Chunk, chunk_markdown, load_corpus
from .retrieve import BM25, CharNgramTfidf, Retriever
from .verify import numbers, verify_claim

__all__ = ["Claim", "Report", "ResearchAgent", "anthropic_writer", "plan_heuristic", "write_extractive", "Chunk",
           "chunk_markdown", "load_corpus", "BM25", "CharNgramTfidf", "Retriever", "numbers", "verify_claim"]
