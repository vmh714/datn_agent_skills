---
name: fastapi-iot-security
description: "Implements JWT Authentication for Web Users and Device Authentication for IoT Edge nodes."
risk: medium
source: workspace
date_added: "2026-04-27"
---

# FastAPI IoT Security

## Overview
This skill establishes the security perimeters of the IoT application. It covers both Human-to-Machine (H2M) security for the Web Dashboard and Machine-to-Machine (M2M) security for the ESP32S3 edge devices.

## Key Responsibilities
- **Manager Authentication (JWT)**:
  - Implementing OAuth2 with Password Flow and Bearer tokens for the Next.js frontend.
  - Password hashing (e.g., using `passlib` with `bcrypt`).
  - Protecting Manager-specific endpoints (e.g., viewing patient data, configuring thresholds).
- **Device Authentication (M2M)**:
  - Providing secure ways for the ESP32S3 firmware to connect (e.g., MQTT Username/Password, pre-shared keys, or X.509 certificates).
  - Validating incoming data payloads to ensure they originate from authenticated devices.

## Conventions & Rules
- **Zero Trust**: Always validate the token on every protected route using FastAPI's dependency injection (`Depends(get_current_user)`).
- **Secret Management**: Never hardcode secrets. Always load JWT secrets, DB passwords, and MQTT credentials from environment variables (`.env`).
- **Rate Limiting**: Implement basic rate limiting on login endpoints to prevent brute-force attacks.

## When to Use
- When building Login/Registration endpoints.
- When creating dependencies for securing routes.
- When configuring MQTT broker authentication mechanisms that interact with the backend.
