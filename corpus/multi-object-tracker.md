# multi-object-tracker

A clear implementation of **SORT-style multi-object tracking**: a constant-velocity Kalman filter per track, IoU-based cost, optimal Hungarian assignment, and a track lifecycle that handles missed detections and false positives. It includes CLEAR-MOT metrics and a synthetic detection generator for testing.

Any detector that outputs bounding boxes (YOLO, a VLM, an event-camera blob detector) can feed it.

## Pipeline per frame

1. **Predict** every track's box with its Kalman filter (state: centre, size and their velocities).
2. **Associate** predictions with detections by maximising IoU (`scipy.optimize.linear_sum_assignment`), rejecting pairs below a threshold.
3. **Update** matched tracks; count misses on unmatched ones.
4. **Manage**: start a tentative track for each unmatched detection, report a track only after `min_hits` matches, and delete it after `max_age` consecutive misses.

## Run

```bash
pip install -e ".[dev]"
python examples/run_tracking.py
pytest
```

Five objects, 120 frames, 15% missed detections, about 1.5 false positives per frame:

```
raw detections : {'MOTA': 0.22, 'precision': 0.721, 'recall': 0.848}
SORT tracker   : {'MOTA': 0.832, 'id_switches': 0, 'precision': 1.0, 'recall': 0.832}
```

The tracker removes every false positive and keeps identities stable through missed frames. The cost is some recall at the start of each track, before it is confirmed.

## Tests

IoU values, Kalman velocity estimation and prediction, identity kept through a missed detection, and better precision and MOTA than raw detections on a noisy scenario.

## Extending

- Appearance embeddings for re-identification after long occlusions (DeepSORT-style)
- Mahalanobis gating using the Kalman innovation covariance
- 3D tracking from LiDAR or stereo

## License

MIT
