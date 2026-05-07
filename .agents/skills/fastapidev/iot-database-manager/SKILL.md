---
name: iot-database-manager
description: "Dual-database management for IoT: PostgreSQL for Relational Metadata and InfluxDB for Time-Series Telemetry."
risk: low
source: workspace
date_added: "2026-04-27"
---

# IoT Database Manager

## Overview
This skill manages the complexity of a dual-database architecture. In our IoT project, relational data (users, devices, settings) is separated from high-frequency time-series data (IMU telemetry, steps, fall events).

## Key Responsibilities
- **PostgreSQL (Metadata)**:
  - Designing SQLAlchemy 2.0 async ORM models.
  - Managing user profiles (Manager role, elderly patients).
  - Storing device configurations (stride length calculation parameters, device status).
  - Managing Alembic migrations.
- **InfluxDB (Time-Series)**:
  - Setting up the InfluxDB Python client (or working via the existing `influxdb-query-manager`).
  - Storing raw IMU telemetry data and computed metrics (distance, walk/run steps).
  - Ensuring fast write throughput.

## Conventions & Rules
- **Separation of Concerns**: Never store 100Hz telemetry in PostgreSQL. Conversely, do not use InfluxDB to store relational user credentials.
- **Connection Pooling**: Use connection pooling for Postgres to prevent exhaustion under load. 
- **Query Optimization**: When querying InfluxDB, utilize Flux/InfluxQL to aggregate data (e.g., downsampling) before returning it to the FastAPI endpoints, to avoid overwhelming the frontend.

## When to Use
- When designing database schemas and relationships.
- When setting up SQLAlchemy models or Alembic configurations.
- When implementing repository patterns to interact with Postgres or InfluxDB.
