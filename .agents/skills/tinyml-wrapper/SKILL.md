---
name: tinyml-wrapper
description: Wraps TinyML models (Edge Impulse/TF Lite) for on-device inference.
---

# TinyML Wrapper

Bridges machine learning with embedded execution via a modular pipeline.

## When to use this skill

- Use this for real-time fall detection on the ESP32S3.
- This is helpful for edge processing and latency reduction.

## How to use it

1. **Modular Engine**: Encapsulate the inference logic in a component that takes an array of floats and returns a classification result.
2. **Event-Driven Inference**: Launch inference only when a data batch is ready (triggered by an event notification from the Sensor Driver).
3. **State Integration**: Feed classification results back into the system FSM (e.g., trigger `STATE_ALERTING` if fall is detected).
4. **Optimized Buffering**: Use a sliding window that shares memory with the sensor data pipeline where possible.
