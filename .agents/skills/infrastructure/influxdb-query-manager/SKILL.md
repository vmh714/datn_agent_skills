---
name: influxdb-query-manager
description: Handles complex time-series queries for device activity history.
---

# InfluxDB Query Manager

Optimizes time-series data retrieval.

## When to use this skill

- Use this for history playback and long-term trend analysis.
- This is helpful for querying raw IMU data efficiently.

## How to use it

1. Utilize Flux language for queries.
2. Filter by bucket, measurement, and tags (device_id).
3. Apply windowing or aggregation for large datasets.
4. Return data in a format ready for the FE charts.
