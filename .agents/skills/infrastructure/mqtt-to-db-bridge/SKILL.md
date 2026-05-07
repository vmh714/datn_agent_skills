---
name: mqtt-to-db-bridge
description: Bridges MQTT messages to persistent storage (Postgres/InfluxDB).
---

# MQTT to DB Bridge

Ensures data persistence and state management.

## When to use this skill

- Use this for background workers that process telemetry.
- This is helpful for decoupling realtime streams from DB writes.

## How to use it

1. Subscribes to MQTT topics (pattern `eldercare/+/+`).
2. Deserializes JSON payloads.
3. Maps data to DB schemas (Telemetery -> Influx, Metadata/Status -> Postgres).
4. Handles connection drops and message queuing.
