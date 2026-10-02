# tsformer-forecast

Transformer-based forecasting for financial time series, with a **walk-forward evaluation harness** that compares every model against simple baselines.

The goal is not a model that looks good in-sample. It is a workflow that tells you honestly whether a deep model adds anything over a ridge regression or a zero forecast.

## What's inside

| Module | Purpose |
|---|---|
| `tsformer/data.py` | synthetic returns with volatility clustering and weak regime-dependent structure; causal features; windowing; expanding walk-forward folds with an optional gap |
| `tsformer/model.py` | compact Transformer encoder (pre-norm, learned positional embedding, last-step read-out) |
| `tsformer/baselines.py` | zero forecast (random walk) and ridge regression on the lookback window |
| `tsformer/train.py` | AdamW, gradient clipping, target scaling, early stopping on a validation block |
| `tsformer/evaluate.py` | MSE, information coefficient (Spearman), directional hit rate; walk-forward comparison |

## Leakage controls

- Labels start strictly after the input window ends (tested).
- Features are causal: changing future data does not change past features (tested).
- The scaler is fit on each fold's training windows only.
- Train / validation / test blocks are time-ordered, with an optional gap between them.

## Run

```bash
pip install -e ".[dev]"
python examples/run_walkforward.py
pytest
```

Typical output on the bundled synthetic series (4 folds, lookback 30):

```
model                mse      IC     hit
zero           4.124e-05   0.000   0.500
ridge          4.322e-05  -0.008   0.501
transformer    4.166e-05  -0.040   0.500
```

Neither model beats the zero forecast here. That is the realistic outcome on noisy return series, and it is exactly what the harness is meant to surface before anything reaches production. To use your own data, build a returns array and pass it through `make_features` and `make_windows`.

## Ideas to extend

- Patch-based inputs (PatchTST-style) and multi-horizon heads
- Cross-sectional training across many assets
- Probabilistic outputs (quantile loss) for position sizing

## License

MIT
