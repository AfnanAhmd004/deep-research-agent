# event-vision-toolkit

Tools for **event-camera (neuromorphic) vision**: simulate events from frames, convert sparse event streams into dense tensors for deep learning, remove background-activity noise, and detect and track fast-moving objects such as satellites and debris crossing a star field.

![Raw events, denoised time surface and tracks](docs/demo.png)

## Contents

| Module | What it does |
|---|---|
| `events` | structured event arrays `(x, y, t, p)`; an idealised log-intensity event simulator; a synthetic space scene (objects + static stars + sensor noise) |
| `representations` | signed or absolute **event frames**, exponential-decay **time surfaces**, bilinear-in-time **voxel grids** |
| `filters` | spatio-temporal **background-activity filter** |
| `detect` | blob detection on short event windows and constant-velocity nearest-neighbour **tracking** |

Static stars produce no events because only brightness *changes* trigger pixels. That property is what makes event sensors attractive for space situational awareness: the background disappears, and moving objects remain.

## Run

```bash
pip install -e ".[dev]"
python examples/space_objects.py --plot
pytest
```

```
events: 23763 raw -> 22595 after background-activity filter
voxel grid shape: (5, 96, 128)
track 0: 12 detections, mean position error 0.59 px
track 1: 12 detections, mean position error 0.39 px
```

## Related work

Background for this toolkit comes from research on neuromorphic sensing for space situational awareness, including:

- Y. Alkendi, H. Elrefaei, A. A. Adil, et al. *Performance Evaluation of CMOS and Event-Based Sensors for Ground-Based Space Situational Awareness.* International Astronautical Congress, 2025.
- Open neuromorphic datasets: [doi:10.57760/sciencedb.28448](https://doi.org/10.57760/sciencedb.28448), [doi:10.57760/sciencedb.29165](https://doi.org/10.57760/sciencedb.29165)

This repository is a small, self-contained toolkit and does not reproduce those studies.

## Tests

Simulator polarity and event counts; voxel grids preserve total polarity; time surfaces are causal and bounded; the filter drops isolated noise and keeps real edges; tracks follow ground truth within a few pixels.

## License

MIT
