# deep-research-agent

A research agent that answers questions from **your own documents** with **citations it can defend**. It plans sub-questions, retrieves with hybrid search, writes claims, **verifies every claim against the passage it cites**, and **abstains** when the documents do not cover the question.

```
question ─► plan (sub-questions) ─► coverage check ──► abstain ("not in the documents")
                                         │ covered
                                         ▼
               hybrid retrieval: BM25 + char n-gram TF-IDF, fused with RRF
                                         ▼
               writer: extractive (offline) or Claude (JSON claims + passage ids)
                                         ▼
               verifier: numbers must appear in the cited passage, content overlap ≥ 60%
                                         ▼
               report: claims [n] · sources · what was not found · how many claims were removed
```

Inspired by tutoring and deep-research assistants, but built around the failure that matters most in technical work: **confident answers with wrong numbers or citations that do not say what is claimed**.

## Example

The bundled corpus is the 31 READMEs of my other repositories: a realistic "ask questions across an engineering portfolio" setting.

```bash
pip install -e ".[dev]"
deep-research "How much earlier does CUSUM detect gearbox wear than a threshold detector, and what is pass^8 on critical cases for agent_v2?"
```

```
- Critical cases, pass^8: agent_v1 100%, agent_v2 40%. [1]
- Pass^8: agent_v1 78.9%, agent_v2 84.2%. [1]
- CUSUM: faults detected 100%, false alarms (healthy robots) 0%, median delay after onset 250 min, ... [2]
- Z-threshold (4σ × 3 samples): faults detected 96%, ..., median delay after onset 560 min, ... [2]

Sources
1. agent-evals › Example: a "better" agent that must not ship
2. robot-ops-agent › Results
```

The compound question was split into two sub-questions, each answered from a different document. Table rows are chunked as self-contained sentences ("row label: column value, …") so they can be cited exactly. Ask something the corpus does not cover ("What is the capital of France?") and the agent says so instead of guessing.

Use Claude as the writer with `--model <model-id>` (`pip install anthropic`, `ANTHROPIC_API_KEY`). Its claims go through the same verifier.

## Evaluation

```bash
python evals/run_eval.py
```

22 answerable questions with gold documents and gold facts, plus 5 off-topic questions. All run fully offline with the extractive writer.

| | |
|---|---|
| retrieval recall@1 / @5: BM25 · char n-grams · hybrid | 100/100 · 95/100 · **100/100** |
| answer contains a gold fact | **16/22 (73%)** |
| cites the gold document | 21/22 |
| claims supported by their cited passage | 41/41 |
| off-topic questions correctly refused | **5/5** |
| answerable questions wrongly refused | 1/22 |

**Verifier stress test.** The sloppy-writer simulation takes the correct claims and corrupts them:

| | caught |
|---|---:|
| a figure changed | **87%** (27/31) |
| claim attached to the wrong passage | **100%** (40/40) |
| correct claims wrongly removed | 0/41 |

All four misses produced a figure that already appears in the cited passage. In two of them the corruption changed nothing (2 → 2); in the other two, "Top-1" became "Top-3" and 5 became 11, both present elsewhere in the same table. A lexical verifier cannot catch these; an LLM judge on top could.

### Honest limits

- I wrote the questions knowing the corpus, so retrieval is easy here (100%). The real difficulty shows up in answer extraction: 6 misses. They come from paraphrase ("five samples" vs "×5"), facts spread across two sentences, and section intros that outscore the specific result. That gap is exactly what an LLM writer closes. The verifier keeps the LLM honest.
- The verifier checks *support*, not *truth*. If a document is wrong, a supported claim is still wrong.
- Lexical verification can reject correct paraphrases. With an LLM writer, prompt it to quote figures exactly, as the bundled prompt does.

## Layout

```
research/corpus.py    markdown → citable chunks (headings, table rows as sentences, console output kept, code dropped)
research/retrieve.py  BM25, char n-gram TF-IDF (stable hashing), RRF fusion, coverage score for abstention
research/agent.py     planner, extractive and Claude writers, verification loop, Report with markdown output
research/verify.py    number and overlap checks
evals/                questions.jsonl and run_eval.py
corpus/               sample corpus (point --corpus at your own .md/.txt folder)
```

## License

MIT
