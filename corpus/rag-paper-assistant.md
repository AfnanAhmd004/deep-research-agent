# rag-paper-assistant

**Retrieval-augmented question answering over research papers**, with every answer tied to the passages it came from. Retrieval, chunking, fusion and evaluation are implemented directly so each step is visible and testable.

## Pipeline

```
papers (.md / .txt / .pdf) ─► sentence-window chunks (with overlap)
                                  │
                ┌─────────────────┴─────────────────┐
             BM25 (lexical)                TF-IDF + SVD (latent)
                └──────── reciprocal-rank fusion ───┘
                                  │
                      top-k chunks with [doc#n] ids
                                  │
                LLM with a cite-or-abstain prompt  (or an extractive fallback)
```

- **Chunking** keeps sentence boundaries and overlaps windows, so an answer that spans a chunk boundary is still retrievable.
- **Hybrid retrieval.** BM25 catches exact terms (e.g. "RRT*", "NEES"); the latent retriever catches paraphrases. Reciprocal-rank fusion combines them without calibrating scores. The latent retriever is a small offline stand-in; swap `LatentRetriever.embed` for any neural embedding model.
- **Grounded generation.** The prompt asks the model to use only the context, cite `[doc#n]`, and say when the answer is not there. Without an LLM, an extractive fallback returns the best-matching cited sentence.

## Run

```bash
pip install -e ".[dev]"          # add ".[pdf]" to index PDFs
python examples/ask.py "How does RRT* rewire the tree?"
pytest
```

```
Q: Why are event cameras useful for space situational awareness?
A: For space situational awareness, event cameras are attractive because satellites and debris
   move quickly against a mostly static star background, and the sensor's sparsity keeps data
   rates low. [event_cameras#2]
```

The bundled `corpus/` holds four short, original notes on event cameras, RRT*, Kalman filtering and backtesting pitfalls. Drop your own papers into the folder to index them.

## Use with an LLM

```python
from ragpaper import PaperAssistant
ast = PaperAssistant.from_folder("papers/", generate=my_llm_fn)   # my_llm_fn(prompt) -> str
print(ast.ask("What representation do you use for events?").text)
```

## Evaluation

`evaluate_retrieval` reports recall@k and mean reciprocal rank over labelled (question, source document) pairs, per retriever. On the four-note demo corpus all three retrievers score 1.0, which is too easy to separate them; the harness is meant for a real paper collection.

## License

MIT
