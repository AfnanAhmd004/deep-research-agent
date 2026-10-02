# pose-graph-slam

**2D pose-graph SLAM** for GPS-denied navigation: noisy odometry and place-recognition loop closures, optimised with sparse **Levenberg–Marquardt**, analytic SE(2) Jacobians and **robust kernels** (Huber, Cauchy) that survive false loop closures.

![Dead reckoning vs L2 vs robust optimisation](docs/demo.png)

## Pipeline

1. **Front end (simulated):** a robot drives three laps of a facility with no GPS. Wheel odometry is noisy, so dead reckoning drifts. When the robot revisits a place, a loop closure gives a relative-pose constraint. Optionally, **false loop closures** model perceptual aliasing, which happens in repetitive environments such as warehouse aisles.
2. **Back end:** minimise `Σ eᵢⱼᵀ Ωᵢⱼ eᵢⱼ` over all poses, where `eᵢⱼ = (xᵢ⁻¹ ⊕ xⱼ) ⊖ zᵢⱼ`:
   - analytic Jacobians of the SE(2) relative-pose residual (checked against finite differences)
   - a sparse block Hessian assembled in COO format and solved with `scipy.sparse.linalg.spsolve`
   - Levenberg damping, with the first pose anchored to fix the gauge freedom
   - **iteratively reweighted least squares** for robust kernels

## Run

```bash
pip install -e ".[dev]"
python examples/run_slam.py --plot
pytest
```

```
181 poses, 180 odometry edges, 107 loop closures
dead reckoning ATE:              5.18 m
optimised ATE:                   0.20 m   (chi2 247348 -> 357 in 5 iters)
with 5 false loops, L2:          9.02 m
with 5 false loops, Cauchy:      0.19 m
```

Loop closures cut trajectory error 25× in five iterations. With only **5 bad matches out of 112**, plain least squares is pulled into a map worse than no SLAM at all. A Cauchy kernel down-weights the outliers and recovers the clean result. That is why production back ends (g2o, GTSAM, Ceres) use robust losses or switchable constraints.

## Tests

SE(2) compose/between consistency, Jacobians against finite differences, error reduction after optimisation, and robustness to false loop closures.

## Extending

- 3D (SE(3)) poses with Lie-algebra updates
- Landmarks and LiDAR scan matching for the front end
- Incremental smoothing (iSAM-style) for online operation

## License

MIT
