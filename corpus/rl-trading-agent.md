# rl-trading-agent

A **Double DQN** trading agent and a minimal **Gymnasium-style environment** for single-asset position-taking, with transaction costs and out-of-sample evaluation.

## Environment

| | |
|---|---|
| Observation | last *N* returns (scaled by the series' volatility) + current position |
| Actions | short / flat / long |
| Reward | `position × next return − cost × |position change|`, scaled by volatility |
| Episodes | random fixed-length slices of the training series |

The position chosen at *t* only earns the return realised after *t*, and costs are charged on every change, so a "flip every bar" policy is penalised.

## Agent

Double DQN (online network selects, target network evaluates), experience replay, Huber loss, gradient clipping, a periodically synced target network and linearly decaying ε-greedy exploration. All in about 100 lines of PyTorch.

## Run

```bash
pip install -e ".[dev]"
python examples/train_dqn.py
pytest
```

Train on the first 70% of an AR(1) return series, then evaluate greedily on the unseen 30%:

```
DQN (out of sample, after costs) Sharpe: 0.64
buy & hold Sharpe:                      0.27
oracle AR(1) rule Sharpe (no costs):     2.63
```

The agent finds part of the structure and beats buy-and-hold after costs, but stays well below the oracle that knows the true model. That gap is typical of RL on noisy financial data and is why the oracle is reported alongside it. The series is synthetic, so this demonstrates the method rather than a market edge.

## Extending

- Continuous position sizing with PPO or SAC
- Multi-asset observations and portfolio-level rewards (e.g. differential Sharpe)
- Walk-forward retraining instead of a single train/test split

## License

MIT
