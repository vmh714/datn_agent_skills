---
name: fastapi-iot-core
description: "Core FastAPI setup for IoT: Dependency Injection, Pydantic Telemetry models, Event-driven async patterns, and CORS."
risk: low
source: workspace
date_added: "2026-04-27"
---

# FastAPI IoT Core

## Overview
This skill focuses on setting up the structural backbone of the FastAPI server specifically tailored for an IoT project (like the Elderly Monitoring system). It ensures the backend can handle high-frequency data (like 100Hz IMU telemetry from MQTT) efficiently without blocking operations.

## Key Responsibilities
- **App Structure**: Configuring the FastAPI `app` instance with standard middleware (CORS, Request ID).
- **Pydantic Validation**: Creating robust Pydantic schemas for Telemetry Data (e.g., Accelerometer, Gyroscope) and Metadata (e.g., Device status, fall alerts).
- **Event-Driven & Async**: Setting up async lifespans for MQTT connection handling and asynchronous background tasks.
- **Dependency Injection**: Managing database sessions and MQTT clients using FastAPI's `Depends()`.

## Conventions & Rules
- **No Blocking Code**: All I/O operations must use `async`/`await`. Avoid `time.sleep()`; use `asyncio.sleep()` if absolutely necessary.
- **Data Validation**: Strict Pydantic v2 validation. All incoming payloads from the Edge (via MQTT->DB Bridge or direct API) must conform to schema.
- **Error Handling**: Use custom HTTPException handlers to return standardized JSON error responses, crucial for frontend parsing and IoT device diagnostics.

## When to Use
- When scaffolding the main `main.py` and `core/` folder (config, exceptions).
- When writing base models for new IoT endpoints.
- When designing the directory structure of the FastAPI project.
