---
name: mqtt-hook-generator
description: Generates React hooks for managing MQTT connections and telemetry data.
---

# MQTT Hook Generator

Handles real-time communication logic.

## When to use this skill

- Use this when integrating MQTT telemetry into a page or component.
- This is helpful for managing high-frequency data streams.

## How to use it

1. Utilize the `mqtt` library (WSS transition).
2. Create subscriptions for specified topics (e.g., `telemetry`, `alert/fall`).
3. Handle message parsing and state updates (Zustand).
4. Implement cleanup (unsubscribing) to prevent memory leaks.
5. Provide a clear API for components to consume (e.g., `isConnected`, `lastMessage`).
