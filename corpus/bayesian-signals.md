# bayesian-signals

Bayesian modelling for **weak, noisy predictive signals**, as in alpha research, plus the statistics needed to tell whether a backtest is real: **online Bayesian linear regression**, **Gaussian processes with automatic relevance determination**, and the **probabilistic and deflated Sharpe ratios**.

## Components

| Module | What it does |
|---|---|
| `BayesianLinearRegression` | conjugate Normal–Inverse-Gamma prior; **exact online updates** (one observation at a time, identical to batch); optional forgetting factor for drifting relationships; Student-t predictive mean **and uncertainty**; credible intervals on coefficients |
| `GaussianProcess` | ARD-RBF kernel with one length-scale per feature, hyperparameters fit by maximising the marginal likelihood (Cholesky, multiple restarts); irrelevant features get pushed to long length-scales |
| `validation` | **PSR** (probability the true Sharpe exceeds a benchmark, adjusted for sample length, skew and kurtosis) and **DSR** (PSR against the Sharpe you would expect from the best of *N* worthless trials) |

## Experiment

`make_data` hides three real signals among 37 noise features, at realistic return-forecasting signal-to-noise (each signal explains well under 1% of variance): a linear one whose strength **halves** mid-sample, a saturating one (`tanh`), and a nonlinear one (`x² − 1`).

```bash
pip install -e ".[dev]"
python examples/research.py      # ~2 min
pytest
```

```
linear ARD top-3:       ['mom', 'flow', 'noise_13']
mutual-information top-6: ['noise_14', 'noise_4', ...] <- unreliable at this signal-to-noise
GP length-scales (short = relevant, 148 = switched off): {'vol_sq': 3.1, 'noise_1': 6.5, 'mom': 8.1,
                                                          'flow': 24.5, 'noise_0': 148.4, 'noise_2': 148.4}
out-of-sample corr with returns: GP 0.192 vs linear ARD 0.075

BLR no forgetting     Sharpe 1st half  2.42 | 2nd half  2.83 | PSR 1.000
BLR forgetting 0.999  Sharpe 1st half  2.36 | 2nd half  2.81 | PSR 1.000

best of 200 noise strategies: annualised Sharpe 0.92, PSR 0.999, deflated SR 0.577
```

### What it shows

1. **Feature screening is fragile at low signal-to-noise.** Linear ARD finds the two linear-ish signals but misses the nonlinear one. Mutual information picks pure noise.
2. **A GP finds what a linear model cannot.** Its shortest length-scale is on the nonlinear `vol_sq` effect, and its out-of-sample correlation is 2.5× the linear model's. Its relevance ranking is still imperfect (one noise feature scores above `flow`), so length-scales are evidence, not proof.
3. **Uncertainty-aware sizing works.** Sizing positions by predictive mean ÷ variance gives a stable walk-forward Sharpe. Forgetting did *not* help here: the decay in one signal was too small relative to the noise for adaptation to pay off.
4. **Selection bias is large.** The best of 200 strategies built on pure noise shows an annualised Sharpe of 0.92 and a naive PSR of 0.999, which looks highly significant. Its deflated Sharpe ratio is 0.58, correctly flagging it as unconvincing once the 200 trials are counted.

Synthetic data with known ground truth, single seed: the goal is a validated research workflow, not a claim about markets.

## License

MIT
