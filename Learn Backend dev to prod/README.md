# OfficeHub V1

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-white.svg">
    <img src="assets/logo.svg" alt="OfficeHub logo" width="140">
  </picture>
</p>

> **A Learning Project for Production-Grade Backend Engineering**

OfficeHub is a learning project that simulates an internal company platform for **room booking and IT ticketing**.

The primary goal of this project is **not to build the most complex application**, but to learn how a real-world software system is designed, secured, tested, monitored, deployed, backed up, and gradually scaled.

---

## Table of Contents

1. [Project Purpose](#-project-purpose)
2. [Implemented Features](#-implemented-features)
3. [Architecture](#-architecture)
   - [Request Flow](#request-flow)
   - [Why Modular Monolith First?](#-why-modular-monolith-first)
4. [Key Design Points](#-key-design-points)
5. [What I Want to Learn](#-what-i-want-to-learn)
   - [1. Backend Engineering](#1-backend-engineering)
   - [2. Frontend Engineering](#2-frontend-engineering)
   - [3. Authentication & Authorization](#3-authentication--authorization)
   - [4. Security Engineering](#-4-security-engineering)
   - [5. Database Engineering](#-5-database-engineering)
   - [6. Application Domain](#-6-application-domain)
   - [7. IT Ticketing](#-7-it-ticketing)
   - [8. Audit Logging](#-8-audit-logging)
   - [9. Observability](#-9-observability)
   - [Request ID](#-request-id)
   - [Logging](#-logging)
   - [10. Backup & Recovery](#-10-backup--recovery)
   - [11. CI/CD](#-11-cicd)
   - [12. Environment Separation](#-12-environment-separation)
   - [13. Testing](#-13-testing)
6. [Planned Future Architecture](#-planned-future-architecture)
7. [Technology Stack](#-technology-stack)
8. [Project Structure](#-project-structure)
9. [Getting Started](#-getting-started)
10. [Endpoints](#endpoints)
11. [Checks](#checks)
12. [Engineering Principles](#-engineering-principles)
13. [Development Philosophy](#-development-philosophy)
14. [Important Note](#-important-note)
15. [Long-Term Goal](#-long-term-goal)

---

## 🎯 Project Purpose

OfficeHub is intentionally designed as a **learning laboratory**.

The project starts from a simple application and gradually introduces production engineering practices.

The learning path is:

```text
Simple Application
       ↓
Modular Monolith
       ↓
Security
       ↓
Testing
       ↓
Observability
       ↓
Backup & Recovery
       ↓
CI/CD
       ↓
Staging
       ↓
Production
       ↓
Performance Engineering
       ↓
Scaling
       ↓
Microservices
       ↓
Event-Driven Architecture
       ↓
Kafka
```

The objective is to understand **why** each technology or architecture is needed, rather than adding technologies simply because they are popular.

---

## ✨ Implemented Features

What is actually built and verified in this repository right now:

**Database**

- PostgreSQL 17 running in Docker (`docker-compose.yml`) with a persistent volume and a healthcheck.
- Migrations managed by **Alembic** (async template); the baseline migration runs cleanly against the real database.

**Backend API (FastAPI)**

- `GET /api/v1/health/live` — liveness probe: the process is up.
- `GET /api/v1/health/ready` — readiness probe: verifies the database connection and returns **503** when the database is down, **200** when healthy.
- **Request ID middleware** — every request receives an `X-Request-ID` (or reuses a well-formed client-provided one) which is echoed back in the response header.
- **Uniform error envelope** for every failed request, following the API contract:

  ```json
  {
    "error": {
      "code": "NOT_FOUND",
      "message": "Not Found",
      "request_id": "req_2d02935c59ab4647b308ab573cf4561c"
    }
  }
  ```

  Internal exception details are never exposed to clients.
- **Environment-driven configuration** via pydantic-settings (`.env` files, 12-factor style) — database URL, CORS origins, log level, environment name.
- **Async database layer** — SQLAlchemy 2 async engine + session factory with `pool_pre_ping`, exposed to handlers through a dependency.

**Frontend**

- Vite + React + TypeScript scaffold with a passing production build (`pnpm build`).

**Engineering baseline**

- `ruff` lint and a `pytest` smoke suite (health probes, error envelope, request ID propagation) — all green.
- `uv.lock` for reproducible installs with uv, plus `requirements.txt` exported from the lockfile so the app can also be installed in a plain venv with pip.

---

## 🏗️ Architecture

Initial architecture:

```text
┌─────────────────────────────┐
│          Frontend           │
│                             │
│ React + TypeScript + Vite   │
└──────────────┬──────────────┘
               │
               │ REST API
               ▼
┌─────────────────────────────┐
│           Backend           │
│                             │
│          FastAPI            │
│                             │
│ ┌─────────┐ ┌─────────────┐ │
│ │  Auth   │ │    Users    │ │
│ ├─────────┤ ├─────────────┤ │
│ │  Rooms  │ │  Bookings   │ │
│ ├─────────┤ ├─────────────┤ │
│ │ Tickets │ │    Audit    │ │
│ └─────────┘ └─────────────┘ │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         PostgreSQL          │
└─────────────────────────────┘
```

This is a **Modular Monolith**: all business modules run inside one FastAPI application, separated by clear domain boundaries — without the operational cost of distributed services.

### Request Flow

How a request currently moves through the system:

```text
HTTP Request
     │
     ▼
Middleware
     ├── Request ID (X-Request-ID in → out)
     └── CORS
     │
     ▼
Router  (/api/v1/...)
     │
     ▼
Handler
     │
     ├── success → {"data": ...} / {"status": ...}
     │
     └── error → Error Handler
                   │
                   ▼
         {"error": {"code", "message", "request_id"}}
     │
     ▼
SQLAlchemy (async session)
     │
     ▼
PostgreSQL
```

Two rules shape this flow:

- The **backend validates everything** — input, permissions, business rules. The frontend is never the security boundary.
- **Every exit path is shaped** — success responses and error responses follow the same contract, and every response carries the request ID.

### 🧩 Why Modular Monolith First?

This project intentionally does **not** start with microservices.

The learning progression is:

```text
Monolith
   ↓
Understand Domain Boundaries
   ↓
Modular Monolith
   ↓
Identify Scaling Problems
   ↓
Extract Services
   ↓
Microservices
```

The goal is to understand the problems that microservices solve.

Not:

```text
"I use microservices because it is modern."
```

---

## 🔑 Key Design Points

Decisions already made (and built) in this codebase — each one is a small problem with a concrete solution.

**1. Port 5432 was already taken**

The machine runs a local PostgreSQL service on 5432, so the Docker database is published on **5433** instead. The connection string lives in configuration (`.env`), never in code — changing environments means changing an environment variable, not a source file.

**2. The first migration has no tables yet**

An empty baseline migration was committed on purpose. It proves the entire pipeline — Alembic → PostgreSQL → `alembic_version` table → version tracking — before any business table exists. When real models arrive, their migration builds on a proven foundation.

**3. Liveness is not readiness**

`/health/live` answers "is the process alive?" — it never touches the database.
`/health/ready` answers "can the process actually serve traffic?" — it runs `SELECT 1` and returns 503 when the database is unreachable. A crash and an infrastructure outage must be distinguishable, or a monitoring system will treat them identically.

**4. One ID traces a whole request**

Every request gets an `X-Request-ID` at the edge of the application and keeps it all the way out:

```text
Client sends/receives X-Request-ID
        ↓
Error envelope carries request_id
        ↓
(Future) application logs, audit records, error tracking carry the same id
```

One identifier correlates a user report with logs, audit trails, and stack traces.

**5. Errors never leak internals**

All failures return the same envelope with a stable machine-readable `code`, a safe `message`, and the `request_id`. A 500 logs the real exception server-side but tells the client only `INTERNAL_ERROR`. Validation failures return field-level errors that are safe to show.

**6. Session cookies, not localStorage**

Authentication is designed around **HttpOnly, Secure cookies** managed by the server — never tokens in `localStorage`, which any injected script can read. Cookie-based sessions require CSRF protection, which is part of the design.

**7. The backend is the security boundary**

Hiding a button in the frontend is a usability decision, not a security one. Every protected endpoint must authenticate, resolve the user's role, check the permission, and check resource ownership before executing logic.

**8. Reproducible installs, two ways**

`uv.lock` pins the exact environment for uv users; `requirements.txt` is exported from the same lockfile for plain `pip install -r`. Same versions either way — no "works on my machine".

---

## 🧠 What I Want to Learn

This project focuses on several areas of backend and software engineering.

## 1. Backend Engineering

Learn how to build a structured backend using:

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- REST API

Topics:

- API design
- Request validation
- Response schemas
- Database transactions
- Repository pattern
- Service layer
- Dependency injection
- Error handling
- Pagination
- Filtering
- Database constraints

## 2. Frontend Engineering

The frontend is built using:

- React
- TypeScript
- Vite
- TanStack Router
- TanStack Query
- Axios
- React Hook Form
- Zod
- shadcn/ui

The goal is to learn how a modern frontend communicates with a backend API.

```text
React
  ↓
TanStack Query
  ↓
Axios
  ↓
REST API
  ↓
FastAPI
  ↓
PostgreSQL
```

## 3. Authentication & Authorization

OfficeHub includes authentication and role-based authorization.

Initial roles:

```text
ADMIN
IT_SUPPORT
EMPLOYEE
```

Example:

```text
EMPLOYEE
 ├── View rooms
 ├── Create booking
 ├── Cancel own booking
 ├── Create ticket
 └── View own tickets

IT_SUPPORT
 ├── View tickets
 ├── Update tickets
 └── Add ticket comments

ADMIN
 ├── Manage users
 ├── Manage rooms
 ├── Manage bookings
 ├── Manage tickets
 └── View audit logs
```

Authentication will use secure server-side session/cookie mechanisms rather than storing authentication tokens in `localStorage`.

## 🔐 4. Security Engineering

Security is treated as part of the application architecture.

The project will cover:

- Authentication
- Authorization
- RBAC
- Password hashing
- Secure cookies
- CSRF protection
- CORS
- Input validation
- Rate limiting
- Security headers
- XSS prevention
- HTTPS
- Secret management
- Audit logging

Basic principle:

```text
Frontend
    ↓
Backend validates everything
    ↓
Authorization
    ↓
Business logic
    ↓
Database
```

The frontend should never be considered the security boundary.

## 🗄️ 5. Database Engineering

Primary database:

```text
PostgreSQL
```

Development:

```text
Docker
  ↓
PostgreSQL
```

Staging and production will use separate database environments.

Example:

```text
Development DB
       │
       ├── Local development
       │
       ▼
Staging DB
       │
       ├── Testing
       │
       ▼
Production DB
```

Topics to learn:

- Database schema design
- Foreign keys
- Unique constraints
- Indexes
- Transactions
- Migrations
- Query optimization
- Connection pooling
- Backup
- Restore
- Data integrity

## 🏢 6. Application Domain

OfficeHub contains two primary business domains.

### Room Booking

Employees can:

- View rooms
- Check availability
- Create bookings
- View bookings
- Cancel bookings

Example:

```text
Employee
   ↓
Select Room
   ↓
Select Date & Time
   ↓
Check Availability
   ↓
Create Booking
   ↓
Booking Confirmed
```

Booking conflicts must be handled by the backend.

Example:

```text
Room A

09:00 ───────── 10:00
       Existing Booking

User requests:

09:30 ───────── 11:00

Result:

409 BOOKING_CONFLICT
```

## 🎫 7. IT Ticketing

Employees can create IT support tickets.

Example lifecycle:

```text
OPEN
  ↓
IN_PROGRESS
  ↓
RESOLVED
  ↓
CLOSED
```

A ticket contains:

```text
Ticket
├── ID
├── Title
├── Description
├── Priority
├── Status
├── Reporter
├── Assignee
├── Created At
└── Updated At
```

Ticket comments are also supported.

## 📋 8. Audit Logging

Important actions should be recorded.

Example:

```text
ADMIN
  │
  ├── CREATE_USER
  ├── UPDATE_USER
  ├── DELETE_USER
  │
EMPLOYEE
  │
  ├── CREATE_BOOKING
  ├── CANCEL_BOOKING
  └── CREATE_TICKET
```

Example audit event:

```json
{
  "actor_id": "user-001",
  "action": "CREATE_BOOKING",
  "resource": "booking",
  "resource_id": "booking-123",
  "request_id": "req-abc123"
}
```

The purpose is to learn:

- Audit trails
- Accountability
- Security investigation
- Operational debugging

## 📈 9. Observability

OfficeHub will introduce observability gradually.

Planned tools:

```text
Prometheus
    ↓
Metrics

Grafana
    ↓
Dashboards

Loki
    ↓
Logs

Sentry / GlitchTip
    ↓
Application Errors
```

The backend will expose:

```text
GET /health/live
GET /health/ready
GET /metrics
```

## 🔎 Request ID

Every request should have a unique request ID.

Example:

```text
Frontend
   │
   │ X-Request-ID
   ▼
FastAPI
   │
   ├── Application Log
   ├── Database Log
   ├── Audit Log
   └── Error Tracking
```

Example:

```text
request_id = req_01JABC123
```

This allows one request to be traced across multiple systems.

## 🪵 Logging

Logs should be structured rather than simple text output.

Example:

```json
{
  "timestamp": "2026-09-29T10:00:00Z",
  "level": "INFO",
  "service": "officehub-api",
  "request_id": "req-123",
  "method": "POST",
  "path": "/api/v1/bookings",
  "status_code": 201,
  "duration_ms": 82
}
```

The goal is to learn how production systems can be debugged without relying on `print()` statements.

## 💾 10. Backup & Recovery

Database backup is part of the learning process.

The project will cover:

```text
PostgreSQL
    ↓
Backup
    ↓
Separate Storage
    ↓
Restore Test
```

Important concepts:

- Backup retention
- Restore testing
- RPO
- RTO
- Disaster recovery

The project should not assume:

> "We have backups, therefore we are safe."

A backup is only useful if it can actually be restored.

## 🚀 11. CI/CD

GitHub Actions will be used to learn CI/CD.

Pipeline:

```text
Git Push
   ↓
GitHub Actions
   ↓
Lint
   ↓
Type Check
   ↓
Unit Tests
   ↓
Integration Tests
   ↓
Security Checks
   ↓
Build
   ↓
Deploy Staging
   ↓
Smoke Test
   ↓
Production
```

The goal is to understand the difference between:

```text
"It works on my machine"
```

and:

```text
"The system can be reliably built and deployed."
```

## 🌎 12. Environment Separation

OfficeHub will have three environments:

```text
Development
     ↓
Staging
     ↓
Production
```

Each environment has separate configuration and resources.

Example:

```text
.env.development
.env.staging
.env.production
```

Secrets must not be committed to Git.

## 🧪 13. Testing

Testing will be introduced progressively.

### Unit Tests

Test isolated business logic.

Example:

```text
calculate_booking_duration()
check_booking_conflict()
validate_ticket_status_transition()
```

### Integration Tests

Test multiple components together.

Example:

```text
API
 ↓
Service
 ↓
Repository
 ↓
PostgreSQL
```

### End-to-End Tests

Test the application from the user's perspective.

Example:

```text
Login
 ↓
Open Rooms
 ↓
Select Room
 ↓
Create Booking
 ↓
Verify Booking
```

---

## 📦 Planned Future Architecture

After the modular monolith is stable, the project may evolve into:

```text
                    ┌──────────────┐
                    │   Frontend   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ API Gateway  │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   Auth Service      Booking Service   Ticket Service
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                         Kafka
```

Potential future technologies:

- Redis
- Kafka
- Microservices
- OpenTelemetry
- Kubernetes
- Message-driven architecture

These are intentionally deferred until the underlying concepts are understood.

---

## 🛠️ Technology Stack

### Frontend

```text
React
TypeScript
Vite
TanStack Router
TanStack Query
Axios
React Hook Form
Zod
shadcn/ui
Sonner
Recharts
date-fns
```

### Backend

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
PostgreSQL
```

### Infrastructure

```text
Docker
PostgreSQL
Prometheus
Grafana
Loki
Sentry / GlitchTip
Nginx
```

### CI/CD

```text
Git
GitHub
GitHub Actions
```

---

## 📁 Project Structure

As it exists in this repository today:

```text
.
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── main.tsx
│   │   └── index.css
│   ├── .env.example
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py            # application factory (create_app)
│   │   ├── core/
│   │   │   ├── config.py      # pydantic-settings configuration
│   │   │   ├── database.py    # async engine + session
│   │   │   ├── errors.py      # error envelope handlers
│   │   │   ├── middleware.py  # X-Request-ID middleware
│   │   │   └── base.py        # shared declarative Base for models
│   │   └── health/
│   │       └── router.py      # /health/live + /health/ready
│   │
│   ├── migrations/            # Alembic (async env.py, versions/)
│   ├── tests/
│   │   └── test_health.py
│   ├── .env.example
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── uv.lock
│   └── alembic.ini
│
├── docker-compose.yml         # PostgreSQL 17 for development
├── .editorconfig
├── .gitignore
└── README.md
```

Modules such as `auth/`, `users/`, `rooms/`, `bookings/`, `tickets/`, and `audit/` will be added under `backend/app/` as they are implemented.

---

## 🚀 Getting Started

Prerequisites: Docker Desktop, [uv](https://docs.astral.sh/uv/) *or* Python 3.10+ venv, Node 20+ with pnpm.

### 1. Database

```sh
docker compose up -d
```

Postgres runs on **port 5433** (5432 is taken by the local PostgreSQL service on this machine).
Credentials: `officehub` / `officehub` / db `officehub`.

### 2. Backend

Option A — uv (recommended):

```sh
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Option B — plain venv + pip:

```sh
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Regenerate `requirements.txt` after changing dependencies:

```sh
uv export --no-hashes --no-emit-project --output-file requirements.txt
```

### 3. Frontend

```sh
cd frontend
pnpm install
pnpm dev
```

Configuration lives in `backend/.env` and `frontend/.env` — copy from the `.env.example` files.

---

## Endpoints

| URL | Purpose |
|---|---|
| http://localhost:8000/api/v1/health/live | liveness |
| http://localhost:8000/api/v1/health/ready | readiness (503 if DB down) |
| http://localhost:8000/docs | OpenAPI docs |
| http://localhost:5173 | frontend dev server |

---

## Checks

```sh
cd backend
uv run ruff check .
uv run pytest
```

---

## 📚 Engineering Principles

### 1. Don't Overengineer

Start simple.

```text
Simple
   ↓
Understand
   ↓
Measure
   ↓
Identify Problem
   ↓
Improve
```

### 2. Security by Design

Security should not be a final feature.

```text
Design
 ↓
Implement
 ↓
Test
 ↓
Monitor
```

### 3. Measure Before Optimizing

Do not optimize based on assumptions.

```text
Problem
   ↓
Measure
   ↓
Analyze
   ↓
Optimize
   ↓
Measure Again
```

### 4. Backups Must Be Tested

A backup that has never been restored is not enough.

```text
Backup
  ↓
Restore
  ↓
Verify
```

### 5. Logs Are Part of the System

Logs should help answer:

```text
What happened?
When did it happen?
Who triggered it?
Which request caused it?
Why did it fail?
```

---

## 🔄 Development Philosophy

The project follows:

```text
Correctness
    ↓
Security
    ↓
Testability
    ↓
Observability
    ↓
Recoverability
    ↓
Deployability
    ↓
Performance
    ↓
Scalability
```

Not:

```text
Microservices
Kafka
Kubernetes
Redis
```

from day one.

---

## 📌 Important Note

OfficeHub is a **learning project**.

Some implementation decisions may intentionally prioritize:

- Learning
- Simplicity
- Experimentation
- Understanding fundamentals

over:

- Maximum performance
- Maximum scalability
- Enterprise complexity

The architecture can evolve as new engineering problems are discovered.

---

## 🚀 Long-Term Goal

The final goal is not simply to have a room booking application.

The goal is to understand how a software system evolves:

```text
                OFFICEHUB LEARNING JOURNEY

Simple App
    │
    ▼
Modular Monolith
    │
    ├── Authentication
    ├── Authorization
    ├── Database
    ├── Testing
    ├── Security
    ├── Logging
    ├── Monitoring
    ├── Backup
    └── CI/CD
    │
    ▼
Production System
    │
    ▼
Performance Problems
    │
    ▼
Scaling Problems
    │
    ▼
Service Boundaries
    │
    ▼
Microservices
    │
    ▼
Event-Driven Architecture
    │
    ▼
Kafka
```

> **The purpose of OfficeHub is to learn the engineering journey, not to skip directly to the final architecture.**
