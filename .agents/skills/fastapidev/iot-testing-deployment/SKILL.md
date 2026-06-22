---
name: iot-testing-deployment
description: "Testing strategies and Dockerization for FastAPI IoT backend."
risk: low
source: workspace
date_added: "2026-04-27"
---

# IoT Testing & Deployment

## Overview
This skill ensures the backend is robust, testable, and ready for deployment in a containerized environment (e.g., for Cloud or local on-prem server).

## Key Responsibilities
- **Testing (Pytest)**:
  - Writing unit tests for critical business logic (e.g., stride length distance calculation).
  - Writing integration tests using `TestClient` or `AsyncClient`.
  - Mocking MQTT inputs and InfluxDB connections to test logic in isolation without requiring actual hardware.
- **Dockerization**:
  - Creating multi-stage `Dockerfile`s optimized for Python.
  - Composing `docker-compose.yml` to orchestrate FastAPI, PostgreSQL, InfluxDB, and the MQTT Broker.

## Conventions & Rules
- **Environment Parity**: The Docker-compose setup should mirror the production environment as closely as possible to catch integration issues early.
- **Stateless Containers**: The FastAPI container should be entirely stateless. All state must reside in Postgres/InfluxDB/Redis.
- **Test Coverage**: Focus testing on complex data transformations and the Alert System (e.g., Fall detection triggers).

## When to Use
- When writing or fixing tests using `pytest`.
- When updating Dockerfiles or `docker-compose.yml`.
- When setting up CI/CD pipeline scripts for the backend.
