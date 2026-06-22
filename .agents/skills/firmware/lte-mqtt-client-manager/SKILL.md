---
name: lte-mqtt-client-manager
description: Manages the A7680C 4G LTE module and MQTT persistence.
---

# LTE MQTT Client Manager

Manages the A7680C 4G LTE module using a Finite State Machine (FSM) and Event-Driven logic.

## When to use this skill

- Use this for devices that communicate over cellular networks.
- This is helpful for managing complex connection states (Network search, MQTT Connect, Reconnect).

## How to use it

1. **Finite State Machine (FSM)**: Implement states: `STATE_POWER_ON`, `STATE_NET_REG`, `STATE_MQTT_CONNECT`, `STATE_IDLE`, `STATE_PUBLISHING`.
2. **Event Handlers**: Use the ESP-IDF Event Loop to dispatch network events (e.g., `LTE_EVENT_CONNECTED`, `LTE_EVENT_DISCONNECTED`).
3. **Mandatory Topics**: Ensure all publishes follow the `instruction.md` schema:
    - `eldercare/dev_{id}/telemetry`
    - `eldercare/dev_{id}/alert/fall`
    - `eldercare/dev_{id}/raw_imu`
4. **Topic Handling**: implement a subscriber callback that routes incoming commands from `eldercare/dev_{id}/cmd` to the internal FSM or specific components.
5. **Modular UART**: Encapsulate AT command logic in a separate component to keep the MQTT logic clean.
