# predictive-maintenance-ts

**Anomaly detection for predictive maintenance** on multi-sensor industrial time series. Four detectors are trained on healthy data only and compared on what matters to a maintenance team: **how early they warn** before a failure and **how often they raise false alarms**.

## Data

A synthetic centrifugal pump with hourly vibration, bearing temperature, discharge pressure, flow and motor current. Sensors follow a daily load cycle and are correlated with each other. Before each of two failures a fault develops over about 150 hours: vibration and temperature rise, flow drops and current climbs. After each failure the pump is repaired.

## Detectors

| Detector | Idea |
|---|---|
| `ZScore` | largest per-sensor deviation from healthy statistics |
| `PCAResidual` | squared prediction error outside the healthy principal subspace: flags broken sensor correlations |
| `IForest` | isolation forest (scikit-learn) |
| `WindowAutoencoder` | PyTorch autoencoder over 12-hour multi-sensor windows; reconstruction error |

Each detector sets its alarm threshold at the 99.5th percentile of its scores on healthy training data. Alarms are **debounced** (three consecutive anomalous hours) to suppress one-off spikes.

## Run

```bash
pip install -e ".[dev]"
python examples/compare_detectors.py
pytest
```

```
detector               lead time per failure (h)   false alarms / week
z-score                                [91, 100]                  0.00
PCA residual (SPE)                      [86, 92]                  0.00
isolation forest                        [51, 46]                  0.00
window autoencoder                    [146, 116]                  0.39
```

The autoencoder warns earliest because it sees the temporal pattern, at the cost of occasional false alarms. The simple statistical detectors are already strong when the fault is visible in single sensors, which is a useful baseline before deploying anything heavier. On real equipment, faults are subtler and healthy data drifts, so thresholds need periodic recalibration.

## Metrics

- **Lead time**: hours between the first alarm in the 200 hours before a failure and the failure itself.
- **False alarms per week**: alarm onsets outside the pre-failure and repair windows.

## License

MIT
