---
name: esp-idf-sensor-driver
description: Develops I2C/SPI drivers and data acquisition logic for ESP-IDF.
---

# ESP-IDF Sensor Driver

Manages hardware interfacing with a modular and event-driven approach.

## When to use this skill

- Use this for integrating the MPU6050 IMU or other sensors.
- This is helpful for achieving precise sampling rates (100Hz) using a non-blocking modular structure.

## How to use it

1. **Modular Init**: Export an init function that returns an `esp_err_t` and handles its own I2C/IO configurations.
2. **Event-Driven Sampling**: Use hardware interrupts (GPIO ISR) or high-resolution timers (esp_timer) to trigger data acquisition.
3. **Internal Buffering**: Use FreeRTOS StreamBuffers or RingBuffers to pass raw data to other modules/tasks.
4. **FSM Integration**: Report sensor health status (READY, ERROR, CALIBRATING) to the system-wide State Machine.
