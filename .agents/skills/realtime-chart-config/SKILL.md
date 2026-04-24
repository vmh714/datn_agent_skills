---
name: realtime-chart-config
description: Configures Recharts for visualizing high-frequency IMU and telemetry data.
---

# Realtime Chart Config

Optimizes data visualization for performance.

## When to use this skill

- Use this for the Realtime Charts on the Data Collection and Device Detail screens.
- This is helpful for displaying 100Hz data (downsampled) smoothly.

## How to use it

1. Define the Recharts `LineChart` or `AreaChart` structure.
2. Configure axes (X: Time/Index, Y: Value range).
3. Implement a sliding window buffer for the data points.
4. Add reference lines for thresholds (e.g., SVM peaks).
5. Optimize rendering frequency to prevent UI lag.
