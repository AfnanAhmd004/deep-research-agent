# market-regime-detection

Detect market regimes with a **Gaussian hidden Markov model written from scratch in NumPy**: Baum–Welch training, forward filtering, forward–backward smoothing and Viterbi decoding. Then use the regimes for allocation **without lookahead**.

## Filtered vs smoothed regimes

| Method | Uses | Safe for trading? |
|---|---|---|
| `filter(X)` | data up to *t* | yes |
| `smooth(X)`, `viterbi(X)` | the whole sample, including the future | no, description only |

Many regime-switching backtests quietly use smoothed states and look far better than anything tradable. Here the allocation example uses `filter`, and a test checks that changing future data leaves past filtered probabilities unchanged.

## Example

```bash
pip install -e ".[dev]"
python examples/regime_allocation.py
pytest
```

The HMM is fit on the first half of a synthetic calm/turbulent market (features: return and log rolling volatility, standardised with training statistics only). On the second half, exposure is set to the filtered probability of the calm regime:

```
filtered regime accuracy (test): 95.50%
buy & hold Sharpe:               1.18
regime-scaled Sharpe:            1.99
```

The regimes here are planted, so this shows the method works when regimes exist. On real markets, regimes are less clean and should be judged on out-of-sample risk reduction rather than accuracy.

## Implementation notes

- Computations are done in log space (`logsumexp`) for numerical stability on long series.
- Means are initialised on quantiles of the first feature, so states start in a sensible order.
- Variance floors prevent collapse onto single points.
- Tests check that EM log-likelihood never decreases, that planted regimes are recovered (>85%), that filtering is causal, and that all probabilities are normalised.

## License

MIT
