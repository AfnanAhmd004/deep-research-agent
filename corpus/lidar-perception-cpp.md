# lidar-perception-cpp

A small, fast **C++17 LiDAR perception library** for ground robots: voxel downsampling, range filtering, **RANSAC ground segmentation**, **Euclidean clustering** with a hashed voxel grid, bounding boxes and a **2.5D traversability grid**. It comes with unit tests, a benchmark, **pybind11 Python bindings** and a CMake build ready for CI.

![Ground segmentation and obstacle clusters](docs/demo.png)

## Pipeline

| Stage | Method | Notes |
|---|---|---|
| `voxel_downsample` | one centroid per occupied voxel (hash map) | O(N) |
| `range_filter` | keep points in a range annulus | removes self-hits and far noise |
| `segment_ground` | RANSAC over near-horizontal planes (tilt limit), early exit, least-squares refit on inliers | rejects walls and box faces as "ground"; handles sloped terrain |
| `euclidean_clusters` | breadth-first search with neighbours from a 27-cell voxel hash | average O(N), no k-d tree dependency |
| `bounding_box` | axis-aligned box per cluster | |
| `traversability_grid` | per-cell min/max/mean height; height spread → traversable / rough / obstacle | input for a cost map or planner |

## Build and test

```bash
cmake -S . -B build && cmake --build build -j
ctest --test-dir build --output-on-failure
./build/lidar_benchmark
```

```
points: 47500
voxel downsample (0.1 m):   8.12 ms -> 41080 points
RANSAC ground:              6.12 ms (200 iterations)
euclidean clustering:       2.89 ms -> 6 clusters
traversability grid:        0.45 ms (80x80 cells)
```

Laptop CPU, single thread, Release build: the full pipeline runs in under 20 ms per scan, inside a 10 Hz LiDAR budget with headroom.

### Python

```bash
pip install pybind11
cmake -S . -B build -DBUILD_PYTHON=ON -Dpybind11_DIR=$(python -m pybind11 --cmakedir) && cmake --build build -j
PYTHONPATH=build python python/demo.py
```

## Tests

The tests run on a synthetic scan with a sloped ground, boxes, cylinders, a rubble patch and sensor noise:

- At least 97% of ground points are recovered, and no obstacle point more than 20 cm above the ground is labelled ground.
- Clustering finds exactly one pure cluster per obstacle.
- Traversability labels open ground, rubble and obstacles correctly.

## Integrating with ROS 2

The core library has no dependencies. Wrapping it in a ROS 2 node means converting `sensor_msgs/PointCloud2` to `lidar::Cloud` in a subscription callback, then publishing ground and obstacle clouds, `vision_msgs/Detection3DArray` boxes, and the traversability grid as a `nav_msgs/OccupancyGrid`. Keeping the algorithms middleware-free makes them unit-testable and reusable on embedded targets.

## License

MIT
