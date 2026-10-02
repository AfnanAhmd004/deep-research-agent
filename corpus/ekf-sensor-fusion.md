# ekf-sensor-fusion

A loosely coupled **GNSS/INS extended Kalman filter** in 2D: IMU-driven prediction at 100 Hz, GNSS position updates at 1 Hz, online **gyro-bias estimation**, and graceful behaviour through a **GNSS outage**. It includes consistency checks (NIS) and a Jacobian test.

![Trajectory and error vs 3σ bound](docs/demo.png)

## Model

| | |
|---|---|
| State | position, velocity, yaw, gyro bias: `[px, py, vx, vy, ψ, b_g]` |
| Prediction | body-frame specific force rotated into the navigation frame; yaw integrates `ω − b_g` |
| Process noise | accelerometer and gyro white noise mapped through the input Jacobian; bias random walk |
| Update | GNSS position, with a Joseph-form covariance update for numerical stability |

## Run

```bash
pip install -e ".[dev]"
python examples/gnss_outage.py --plot
pytest
```

A 120 s drive with a 20 s outage between 60 and 80 s. The IMU has a constant gyro bias the filter has to learn:

```
position RMSE  fused:   1.10 m   IMU only:    37.17 m
max error during outage (fused): 1.22 m
estimated gyro bias: 0.0097 rad/s (true 0.01)
mean NIS: 2.05 (expected ~2 for 2-D GNSS fixes)
```

During the outage the filter keeps predicting from the IMU alone. Its 3σ bound widens to reflect the growing uncertainty, then collapses as soon as GNSS returns. A mean NIS close to 2 (chi-square with 2 degrees of freedom) shows the noise models are consistent.

## Tests

- The analytic state-transition Jacobian matches central finite differences.
- Fused error is at least five times lower than IMU-only dead reckoning.
- Uncertainty grows during the outage and shrinks after it.
- Mean NIS falls within the expected range.
- Gyro bias converges to its true value.

## Extending

- 3D strapdown mechanisation with quaternions and accelerometer biases
- Error-state (indirect) formulation
- Tightly coupled pseudorange updates, or visual-inertial odometry as an alternative aid

## License

MIT
