# purged-cv

Leakage-safe cross-validation for financial machine learning: **purged K-fold with embargo** and **combinatorial purged cross-validation (CPCV)**, with scikit-learn-compatible splitters.

## The problem

Financial labels usually span time: "the 20-day forward return from day *t*" depends on prices up to *t + 20*. With ordinary shuffled K-fold, a training sample from day *t + 1* shares 19 of those 20 days with a test sample from day *t*. A flexible model learns that overlap, and the cross-validated score looks like an edge that does not exist.

```bash
pip install -e ".[dev]"
python examples/leakage_demo.py
```

```
shuffled K-fold accuracy : 0.794  (looks like an edge)
purged K-fold accuracy   : 0.400
CPCV accuracy            : 0.478 +/- 0.052 over 15 paths
A random walk has no edge: honest accuracy should be close to 0.5.
```

The prices are a pure random walk. Shuffled K-fold reports about 79% accuracy; purged methods bring it back to around chance. (Purged K-fold lands somewhat below 0.5 here because the time-index feature makes the forest extrapolate badly into each held-out block.)

## Usage

```python
from purgedcv import PurgedKFold, CombinatorialPurgedCV, forward_return_labels
from sklearn.model_selection import cross_val_score

y, t1 = forward_return_labels(close, horizon=20)    # t1[i] = when label i ends
cv = PurgedKFold(n_splits=5, t1=t1, embargo_pct=0.01)
scores = cross_val_score(model, X, y, cv=cv)

cpcv = CombinatorialPurgedCV(n_groups=6, n_test_groups=2, t1=t1)  # 15 train/test paths
```

- **Purging** removes training samples whose label window overlaps any test window.
- **Embargo** also drops a buffer of samples right after each test block.
- **CPCV** tests every combination of *k* out of *N* blocks, giving a distribution of out-of-sample scores instead of a single number.

Method: M. López de Prado, *Advances in Financial Machine Learning* (Wiley, 2018), chapters 7 and 12. This is an independent implementation.

## Tests

Overlap is checked against a brute-force definition; the embargo removes exactly the expected samples; in CPCV every sample is tested the same number of times.

## License

MIT
