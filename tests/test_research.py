import re
import subprocess
import sys
from pathlib import Path

import pytest

from research import Claim, ResearchAgent, Retriever, chunk_markdown, load_corpus, numbers, verify_claim
from research.cli import main as cli

ROOT = Path(__file__).resolve().parent.parent

DOC = """# Widget study

The widget controller reduces vibration by 42% compared with the baseline PID loop.

| method | vibration | cost |
|---|---|---|
| PID | 1.00 | low |
| adaptive | 0.58 | medium |

```
benchmark: adaptive 0.58 vs pid 1.00
```

```python
import os
secret = os.environ["X"]
```

## Limits

Tested only at room temperature; humidity was not controlled.
"""


@pytest.fixture
def mini(tmp_path):
    (tmp_path / "widget.md").write_text(DOC)
    (tmp_path / "other.md").write_text("# Gardening\n\nTomatoes need six hours of direct sunlight every day to fruit well.\n")
    return Retriever(load_corpus(tmp_path))


def test_chunking_keeps_tables_and_output_but_not_code():
    text = " ".join(c.text for c in chunk_markdown("widget", DOC))
    assert "Adaptive: vibration 0.58, cost medium." in text
    assert "Benchmark: adaptive 0.58 vs pid 1.00." in text
    assert "secret" not in text and "import" not in text
    assert any(c.heading == "Limits" for c in chunk_markdown("widget", DOC))


def test_numbers_are_normalised():
    assert numbers("cut 6.19 to 2.73 bps, 1,000 runs, +13 points") == {"6.19", "2.73", "1000", "13"}


def test_verifier():
    src = "The widget controller reduces vibration by 42% compared with the baseline PID loop."
    assert verify_claim("The widget controller reduces vibration by 42%.", src).supported
    v = verify_claim("The widget controller reduces vibration by 24%.", src)
    assert not v.supported and "24" in v.reason
    assert not verify_claim("Tomatoes need six hours of sunlight.", src).supported


def test_agent_answers_with_citations_and_abstains(mini):
    agent = ResearchAgent(mini)
    rep = agent.run("How much does the widget controller reduce vibration?")
    assert rep.claims and all(c.supported for c in rep.claims)
    assert any("42%" in c.text for c in rep.claims)
    md = rep.markdown()
    assert "[1]" in md and "widget" in md.split("**Sources**")[1]
    off = agent.run("Who painted the Mona Lisa?")
    assert off.abstained and "do not contain enough information" in off.markdown()


def test_unsupported_claims_are_dropped(mini):
    def sloppy(question, sub, hits):
        cid = hits[0][0].id
        return [Claim("The widget controller reduces vibration by 90%.", [cid]),
                Claim("The widget controller reduces vibration by 42%.", [cid]),
                Claim("It also cures headaches.", ["nonexistent#0"])]

    rep = ResearchAgent(mini, writer=sloppy).run("How much does the widget controller reduce vibration?")
    assert [c.text for c in rep.claims] == ["The widget controller reduces vibration by 42%."]
    assert len(rep.dropped) == 2 and "removed by verification" in rep.markdown()


def test_eval_suite_quality_does_not_regress():
    out = subprocess.run([sys.executable, str(ROOT / "evals" / "run_eval.py")], capture_output=True, text=True,
                         timeout=600).stdout
    assert re.search(r"hybrid\s+100%\s+100%", out)
    hits = int(out.split("answer contains a gold fact")[1].split("/")[0])
    assert hits >= 15
    assert "correctly abstained (off-topic)  5/5" in out


def test_cli(capsys):
    assert cli(["What is the deflated Sharpe ratio of the best of 200 noise strategies?",
                "--corpus", str(ROOT / "corpus")]) == 0
    assert "bayesian-signals" in capsys.readouterr().out
