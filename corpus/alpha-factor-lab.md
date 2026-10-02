# alpha-factor-lab

A compact toolkit for **cross-sectional alpha research**: define factors, then measure whether they predict returns with information coefficients, IC decay, quantile portfolios, turnover and IC-weighted combination.

It ships with a synthetic 200-stock panel that has **known, planted effects** (momentum, short-term reversal, low volatility), so you can check that the pipeline recovers real effects and does not flag noise.

## Example

```bash
pip install -e ".[dev]"
python examples/factor_report.py
```

```
factor            meanIC      t   IC>0  LS Sharpe  turnover
momentum_6_1       0.016    6.2   0.58       2.99      0.08
reversal_5d        0.020    8.8   0.62       4.17      0.35
low_vol_63d        0.005    2.3   0.53      -0.08      0.03
trend_quality      0.003    1.5   0.52       1.03      0.10
combined           0.025   10.2   0.65       4.87      0.26
```

A few things this table shows, all of which carry over to real data:

- **Reversal** has the strongest daily IC but four times the turnover of momentum, so costs matter much more for it.
- **Low volatility** has a positive IC but a flat long–short spread: a factor can rank well on average and still fail to make money at the extremes.
- **Combining** factors with lagged IC weights gives a higher, more stable IC than any single factor.
- Momentum's IC **grows with horizon** (0.016 at 1 day, 0.074 at 21 days), so it suits slower rebalancing.

Numbers come from synthetic data with planted premia. They demonstrate the method, not a tradable edge.

## Adding a factor

```python
from afl import factor

@factor("my_signal")
def my_signal(prices):            # wide frame: dates x assets
    return prices.pct_change(10)  # use only past data
```

## What the tests check

- A planted factor is recovered with a significant t-stat; a random factor is not.
- Factors are point-in-time: changing future prices leaves past scores unchanged.
- The IC of a perfect signal is 1.

## License

MIT
