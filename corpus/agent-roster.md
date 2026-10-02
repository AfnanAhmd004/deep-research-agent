# agent-roster

A library of **17 specialist AI agents** for robotics, machine learning, quantitative trading and engineering leadership. Each one is a reviewed, tested definition rather than a one-line persona. The library comes with a **router** that picks the right specialist for a task, **playbooks** that chain specialists into workflows with gates, and validators that run in CI.

The agents install directly as **Claude Code subagents**. They also export as plain system prompts for any chat API or agent framework.

## The roster

| Division | Agent | Use it for |
|---|---|---|
| engineering | [`code-reviewer`](agents/engineering/code-reviewer.md) | Review a diff or pull request for correctness, tests, readability and maintainability before merge; reports findings ranked by severity with concrete fixes. |
| engineering | [`embedded-cpp-engineer`](agents/engineering/embedded-cpp-engineer.md) | Real-time and embedded C++ - ROS 2 nodes, performance optimisation, memory and latency profiling, CMake builds, cross-compilation, and porting Python prototypes to production C++. |
| engineering | [`llm-engineer`](agents/engineering/llm-engineer.md) | Building LLM and VLM features - prompting, RAG, tool-using agents, fine-tuning (LoRA/QLoRA), alignment (DPO), structured outputs, and reducing hallucination, latency or cost. |
| engineering | [`mlops-engineer`](agents/engineering/mlops-engineer.md) | Training pipelines, model serving, inference optimisation, data and model versioning, monitoring for drift, GPU cost, and CI/CD for machine-learning systems. |
| engineering | [`motion-planning-controls-engineer`](agents/engineering/motion-planning-controls-engineer.md) | Path and trajectory planning, MPC, LQR, PID tuning, manipulator and mobile-robot control, multi-robot coordination, and stability or tracking-error problems. |
| engineering | [`robotics-perception-engineer`](agents/engineering/robotics-perception-engineer.md) | Camera, LiDAR, radar and event-camera perception on robots - detection, segmentation, tracking, calibration, sensor fusion at the object level, and perception latency or failure analysis. |
| engineering | [`security-reviewer`](agents/engineering/security-reviewer.md) | Security review of code, infrastructure and AI features - secrets, authentication, injection (including prompt injection), data exposure, supply chain, and robot or OT network exposure. |
| engineering | [`state-estimation-engineer`](agents/engineering/state-estimation-engineer.md) | Localisation, odometry, SLAM and sensor fusion - Kalman filters, factor graphs, IMU/GNSS/wheel/visual fusion, loop closure, and diagnosing drift or filter divergence. |
| research | [`experiment-auditor`](agents/research/experiment-auditor.md) | Check an experiment or evaluation for leakage, unfair baselines, too few seeds, p-hacking, and conclusions that the evidence does not support, before results are shared. |
| research | [`research-scientist`](agents/research/research-scientist.md) | Turn an open problem into a research plan - literature review, hypotheses, method selection, experiment design, and writing up results for papers, grants or internal reports. |
| quant | [`backtest-auditor`](agents/quant/backtest-auditor.md) | Audit a trading backtest for lookahead bias, survivorship bias, unrealistic fills and costs, overfitting and selection bias (deflated Sharpe) before it is trusted or traded. |
| quant | [`execution-risk-manager`](agents/quant/execution-risk-manager.md) | Execution algorithms (TWAP, VWAP, implementation shortfall), market impact, position limits, risk controls, kill switches and pre-trade checks for automated trading systems. |
| quant | [`quant-researcher`](agents/quant/quant-researcher.md) | Alpha research - signal ideas, feature engineering, factor and time-series models, ML/transformer forecasting, walk-forward evaluation and portfolio construction for systematic trading. |
| leadership | [`cto-advisor`](agents/leadership/cto-advisor.md) | Technology strategy and leadership decisions - build vs buy, roadmap prioritisation, team structure and hiring, technical due diligence, risk, budgets, and explaining technical trade-offs to boards and investors. |
| leadership | [`systems-architect`](agents/leadership/systems-architect.md) | End-to-end system design - service and data architecture, robot software stacks, edge vs cloud split, interfaces and APIs, scalability, reliability targets and architecture decision records. |
| operations | [`incident-commander`](agents/operations/incident-commander.md) | During a production or field incident - outages, a robot fleet down, a model misbehaving, or a trading system fault - to coordinate response, communication, mitigation and the blameless postmortem. |
| operations | [`robot-safety-engineer`](agents/operations/robot-safety-engineer.md) | Functional safety of robots and autonomous machines - hazard analysis, risk assessment, safety functions, human-robot collaboration, interlocks, and how AI components fit into a safety case. |

Every agent follows the same structure, which the validator enforces:

- **Mission**: one sentence
- **Use me for**: concrete scenarios
- **Operating principles**: the judgement that separates a senior specialist from a generic assistant
- **Workflow**
- **Deliverables**
- **Guardrails**
- **Handoffs** to other agents

Reviewers and auditors are **read-only by construction**: the validator rejects them if they have Edit or Write tools.

## Playbooks

Multi-agent workflows with explicit inputs, outputs and **gates** (a gate must pass before the next step starts). The validator checks that every input a step needs was produced by an earlier step.

| Playbook | Goal | Agents |
|---|---|---|
| `field-incident` | A robot fleet is misbehaving at a customer site; restore safe operation and prevent recurrence. | incident-commander → robot-safety-engineer → state-estimation-engineer → incident-commander |
| `research-to-product` | Turn a promising research result into a tested component a product team can own. | research-scientist → experiment-auditor → embedded-cpp-engineer → code-reviewer |
| `robot-cell-commissioning` | Commission a new collaborative robot cell with perception-based safety and an LLM operator assistant. | systems-architect → robot-safety-engineer → robotics-perception-engineer → llm-engineer → robot-safety-engineer |
| `ship-ml-model` | Take a trained model from "works in a notebook" to a monitored production release. | experiment-auditor → mlops-engineer → security-reviewer → cto-advisor |
| `strategy-to-live` | Move a systematic trading idea from research to small live capital without fooling ourselves. | quant-researcher → backtest-auditor → execution-risk-manager → cto-advisor |

```bash
roster playbook strategy-to-live
```

## Usage

```bash
pip install -e ".[dev]"
roster list
roster route "our EKF diverges whenever GNSS drops out under the bridge"
roster install --target .claude/agents                       # all agents, as Claude Code subagents
roster install --target .claude/agents --only quant-researcher backtest-auditor
roster export agents.json                                     # system prompts for any LLM API
roster validate                                               # CI: schema, sections, tools, handoffs, playbooks
pytest
```

## Routing

`Router` is BM25 over each agent's keywords, name, description and body, with field weights. It needs no embeddings and no network, so it is instant and deterministic. `route_with_fallback` asks a model to choose among the top candidates **only when BM25 is ambiguous** (the top two scores are close). Routing therefore costs nothing in the common case and stays accurate in the hard ones.

Measured on [`data/routing_eval.jsonl`](data/routing_eval.jsonl): 51 hand-written tasks, three per agent, written *before* any tuning and phrased the way people actually ask.

| | BM25 only |
|---|---:|
| top-1 accuracy | 82% |
| top-3 accuracy | 92% |

The misses are informative:
- "We tried 40 variants and report the best, is that fair?" → `backtest-auditor` instead of `experiment-auditor`, which is arguably a fine answer.
- "Coordinate three drones so their paths never conflict" → `incident-commander`, because the word "coordinate" was taken too literally.

That second miss is the case the LLM fallback exists for. The eval set is a regression test, not a tuning target: improving routing on it directly would overfit, so changes should be validated on new tasks.

## Layout

```
agents/<division>/<name>.md   agent definitions (YAML frontmatter + Markdown)
playbooks/*.yaml              multi-agent workflows with gates
roster/library.py             parsing, validation, Claude Code install, JSON export
roster/router.py              BM25 router, evaluation, LLM fallback
roster/playbooks.py           playbook loading, validation, Mermaid export
data/routing_eval.jsonl       labelled routing tasks
```

## License

MIT
