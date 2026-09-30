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

**Phase status**

| Phase | Scope | Status |
|---|---|---|
| 00 | Project Initialization | ✅ done |
| 01 | Backend Foundation | ✅ done |
| 02 | Frontend Foundation | ✅ done |
| 03 | Authentication | ✅ done |
| 04 | Authorization & RBAC | ✅ done |
| 05 | Room Management | ✅ done |
| 06 | Booking | ✅ done |
| 07+ | Ticketing, observability, security hardening, CI/CD | ⬜ not started |

**Database**

- PostgreSQL 17 as the development database. Development runs against the **local PostgreSQL
  service**; `docker-compose.yml` remains available as an alternative.
- Migrations managed by **Alembic** (async template); the baseline migration runs cleanly against
  the real database.
- `users`, `roles`, `user_roles`, and `sessions` tables (Phase 03).
- `scripts/seed_dev.py` creates the three roles plus one development admin, idempotently.
- Tests run against a **separate `officehub_test` database**, created and migrated automatically by
  `tests/conftest.py`, so a test run can never touch development data.

**Backend API (FastAPI)**

- `GET /api/v1/health/live` — liveness probe: the process is up.
- `GET /api/v1/health/ready` — readiness probe: verifies the database connection and returns **503** when the database is down, **200** when healthy.
- **Authentication (Phase 03)** — `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`,
  `GET /auth/csrf`, matching the API contract in the PRD.
- **Session cookies, not tokens** — the session lives in an `HttpOnly`, `SameSite=Lax` cookie that
  becomes `Secure` in production. The raw token is never stored: the database only holds a SHA-256
  hash, so a database leak cannot hand out live sessions.
- **Password hashing** — Argon2id via `argon2-cffi`. An unknown email is still verified against a
  dummy hash so a missing account costs the same time as a wrong password.
- **CSRF protection** — double-submit cookie. The browser reads the `csrf_token` cookie and echoes
  it in `X-CSRF-Token`; the server compares them with `secrets.compare_digest` on every
  `POST`/`PUT`/`PATCH`/`DELETE`.
- **Session revocation** — logout stamps `revoked_at`; expired or revoked sessions authenticate
  nothing.
- **Authorization & RBAC (Phase 04)** — a permission catalog (`resource:action`), a role →
  permission mapping, and a `require_permissions(...)` dependency. Routes ask for a permission
  instead of naming a role, so renaming a role never touches a route.
  - `GET /api/v1/users` — requires `users:read`. ADMIN passes, EMPLOYEE and IT_SUPPORT get **403**.
  - `GET /api/v1/users/{user_id}` — ownership first: reading your own account needs no permission;
    reading someone else's needs `users:read`.
- **Room management (Phase 05)** — full CRUD behind permissions, plus the rooms UI.
  - `GET /api/v1/rooms` — requires `rooms:read`. EMPLOYEE sees **ACTIVE** rooms only; whoever may
    also change rooms sees the disabled ones as well.
  - `POST`, `PATCH`, `DELETE` — `rooms:create` / `rooms:update` / `rooms:delete` (ADMIN).
  - `PATCH` is a true partial update: `exclude_unset` keeps "field omitted" distinct from
    "field set to null", so omitted fields survive. An empty patch is rejected with **422**.
  - Frontend: `/rooms` list, `/rooms/new`, `/rooms/$roomId` (inline edit, enable/disable, delete).
    The write controls render only for ADMIN — usability only; the API re-checks everything.
- **Booking (Phase 06)** — creation, cancellation, availability, and a real transaction.
  - **Overlap is a database constraint, not application code.**
    `bookings_no_overlap_per_room` is a PostgreSQL exclusion constraint over
    `btree_gist (room_id, tstzrange(start_time, end_time, '[)'))` with
    `WHERE (status = 'CONFIRMED')`. A `SELECT … WHERE not exists` check has a race:
    two requests can both find the slot free and both insert. Only the database can arbitrate.
  - The service turns that refusal into **409 `BOOKING_CONFLICT`**, matched on SQLSTATE `23P01`
    (SQLAlchemy replaces asyncpg's exception class with its own dialect wrapper).
  - `[)` means **10:00–11:00 and 11:00–12:00 do not overlap** — back-to-back bookings are legal, and
    there is a test that says so.
  - **Booking and audit log commit together.** One `commit()`, one `rollback()`; a rejected booking
    leaves no audit row claiming success. (Uses `commit()`/`rollback()` rather than
    `async with session.begin()`, because SQLAlchemy begins a transaction implicitly on the first
    read — `begin()` would raise as soon as the service fetched the room first.)
  - Rejections use domain codes: `BOOKING_CONFLICT`, `ROOM_INACTIVE`, `INVALID_TIME_RANGE`,
    `ROOM_NOT_FOUND`, `BOOKING_NOT_CANCELLABLE`.
  - `GET /api/v1/bookings` — an employee sees only their own; an admin sees all. Filters: `room_id`,
    `status`, `day`, with `page` / `page_size` and a `meta` block.
  - `DELETE /api/v1/bookings/{id}` cancels (soft, 204) — ownership first, then the state change.
- **Audit logging (Phase 06)** — `audit_logs` records actor, action, resource, before/after JSONB
  snapshots, IP, user agent, and the request ID. `GET /api/v1/audit-logs` is ADMIN-only (`audit:read`).
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
- **Environment-driven configuration** via pydantic-settings (`.env` files, 12-factor style) — database URL, CORS origins, log level, environment name, session TTL.
- **Async database layer** — SQLAlchemy 2 async engine + session factory with `pool_pre_ping`, exposed to handlers through a dependency.

**Frontend**

- Vite + React 19 + TypeScript with **TanStack Router** (code-based routes), **TanStack Query**,
  **Axios**, and **Tailwind CSS v4**.
- shadcn/ui-style primitives (`Button`, `Input`, `Label`, `Card`) with CSS-variable design tokens, so
  restyling happens in `src/index.css` rather than in component code.
- **API client** — one Axios instance with `withCredentials`, plus a request interceptor that attaches
  the CSRF header on unsafe methods, and an `ApiError` type that reads the backend's error envelope.
- **Dashboard shell** — sidebar, header, sign-out, and a protected route.
- **Rooms UI (Phase 05)** — list, create form, and detail page with inline edit.
- **Booking workflow (Phase 06)** — availability panel and booking form on the room page, plus
  `/bookings` with per-booking cancel.
- **Route guard** — a pathless `app` layout route resolves the session in `beforeLoad` and
  redirects anonymous visitors to `/login`, so a protected page never flashes.
- **Error boundary and loading states** — the root route owns a `notFoundComponent` and an
  `errorComponent`; routes declare `pendingComponent`.

**Engineering baseline**

- `ruff` lint and a `pytest` suite — **68 passing**: health probes, error envelope, request ID
  propagation, login/logout/session/CSRF, the role matrix, room CRUD, booking overlap rules,
  ownership, and audit atomicity.
- `uv.lock` for reproducible installs with uv, plus `requirements.txt` exported from the lockfile so the app can also be installed in a plain venv with pip.
- `pnpm build` (TypeScript project build + Vite production build) and `oxlint` both pass.


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

**1. The connection string lives in configuration**

Development points at the machine's local PostgreSQL service. The connection string is read from `.env`, never from code — switching environments means changing an environment variable, not a source file.

**2. The first migration has no tables yet**

An empty baseline migration was committed on purpose. It proves the entire pipeline — Alembic → PostgreSQL → `alembic_version` table → version tracking — before any business table exists. The `users`/`roles`/`sessions` migration then builds on a proven foundation.

**One trap this exposed:** the development database is shared with another project, so `alembic revision --autogenerate` cheerfully proposed dropping tables it had never heard of. The migration was hand-trimmed down to the four tables it owns. A migration must only ever touch what it created.

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

Two different secrets, two different strategies:

```text
password              → Argon2id, slow and memory-hard, because a human chose it
session / csrf token  → SHA-256, because we generated it from a CSPRNG
```

The database stores only the **hash** of a session token. A dump of the `sessions` table therefore
hands an attacker nothing usable, which is why a leaked backup does not mean a mass logout.

CSRF uses the **double-submit cookie** pattern: the server sets a readable `csrf_token` cookie, the
client echoes it in `X-CSRF-Token`, and the server compares the two with
`secrets.compare_digest`. An attacker on another origin can make the browser send the request but
cannot read the cookie to copy it into a header.

**7. Login says nothing about what failed**

A wrong password and an unknown account return the same status, the same code, and the same message.
An unknown email is still verified against a dummy hash, so the two cases also take the same time.
Login throttling and rate limiting are *not* implemented yet — that is Phase 08.

**8. The backend is the security boundary**

Hiding a button in the frontend is a usability decision, not a security one. Every protected endpoint must authenticate, resolve the user's role, check the permission, and check resource ownership before executing logic.

```text
Request
  ↓
authenticated?          get_current_user      → 401
  ↓
has the permission?      require_permissions   → 403
  ↓
owns the resource?       per-route check       → 403
  ↓
handler
```

Two guards rather than one, because they answer different questions. A permission says *"this role
may list every account"*; ownership says *"this account may read this particular record"*, and only
the route knows what "own" means for its data. `GET /users/{user_id}` shows both: reading yourself
needs no permission at all.

**9. Reproducible installs, two ways**

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
│   │   ├── components/
│   │   │   ├── app-shell.tsx      # sidebar + header
│   │   │   └── ui/                # button, input, label, card
│   │   ├── features/
│   │   │   ├── auth/          # session query, login/logout, requireUser guard
│   │   │   ├── bookings/      # booking queries + availability/book form panel
│   │   │   └── rooms/         # room queries and mutations
│   │   ├── lib/
│   │   │   ├── api/client.ts      # axios instance + CSRF interceptor
│   │   │   ├── api/errors.ts      # ApiError over the error envelope
│   │   │   └── utils.ts           # cn()
│   │   ├── routes/
│   │   │   ├── __root.tsx         # layout, notFound, error boundary
│   │   │   ├── app.tsx            # pathless authenticated layout + guard
│   │   │   ├── dashboard.tsx
│   │   │   ├── index.tsx          # redirects to /dashboard
│   │   │   ├── login.tsx
│   │   │   ├── bookings/
│   │   │   │   └── index.tsx      # my bookings + cancel
│   │   │   └── rooms/
│   │   │       ├── index.tsx      # list
│   │   │       ├── new.tsx        # admin create
│   │   │       └── $roomId.tsx    # detail + inline edit
│   │   ├── index.css              # tailwind + design tokens
│   │   ├── main.tsx
│   │   └── router.tsx             # code-based route tree
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
│   │   │   ├── middleware.py  # X-Request-ID + CSRF middleware
│   │   │   ├── permissions.py # permission catalog + role mapping (Phase 04)
│   │   │   ├── security.py    # argon2 hashing, token generation
│   │   │   └── base.py        # shared declarative Base for models
│   │   ├── auth/
│   │   │   ├── models.py      # User, Role, Session, user_roles
│   │   │   ├── schemas.py     # request/response schemas
│   │   │   ├── repository.py  # database access
│   │   │   ├── service.py     # authenticate / session lifecycle
│   │   │   ├── dependencies.py# get_current_user, require_permissions
│   │   │   └── router.py      # /auth/* endpoints
│   │   ├── audit/
│   │   │   ├── models.py       # AuditLog + AuditAction
│   │   │   ├── router.py       # /audit-logs (ADMIN)
│   │   │   └── service.py      # record() — never commits, caller owns the transaction
│   │   ├── bookings/
│   │   │   ├── models.py       # Booking + no-overlap exclusion constraint
│   │   │   ├── repository.py
│   │   │   ├── router.py       # /bookings, availability
│   │   │   ├── schemas.py
│   │   │   └── service.py      # create/cancel inside one transaction
│   │   ├── rooms/
│   │   │   ├── models.py       # Room + RoomStatus
│   │   │   ├── repository.py
│   │   │   ├── router.py       # /rooms/* CRUD
│   │   │   └── schemas.py      # create / partial update / response
│   │   ├── users/
│   │   │   ├── repository.py
│   │   │   ├── router.py      # /users/* — first RBAC-protected endpoints
│   │   │   └── schemas.py
│   │   └── health/
│   │       └── router.py      # /health/live + /health/ready
│   │
│   ├── migrations/            # Alembic (async env.py, versions/)
│   ├── scripts/seed_dev.py    # roles + one development admin
│   ├── tests/
│   │   │   ├── conftest.py        # separate test database + fixtures
│   │   │   ├── test_auth.py
│   │   │   ├── test_audit.py
│   │   │   ├── test_bookings.py
│   │   │   ├── test_health.py
│   │   │   ├── test_rooms.py
│   │   │   └── test_users.py      # the role matrix
│   ├── .env.example
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── uv.lock
│   └── alembic.ini
│
├── docker-compose.yml         # optional PostgreSQL 17 alternative
├── .editorconfig
├── .gitignore
└── README.md
```

Modules such as `rooms/`, `bookings/`, `tickets/`, and `audit/` will be added under `backend/app/`
as they are implemented.

---

## 🚀 Getting Started

Prerequisites: [uv](https://docs.astral.sh/uv/) *or* Python 3.10+ venv, Node 20+ with pnpm, and a
running PostgreSQL 17.

### 1. Database

Development uses the **local PostgreSQL service** on port 5432. Point `DATABASE_URL` at your
database in `backend/.env`, then create it once:

```sql
CREATE DATABASE officehub;
```

Optional alternative — the containerized database:

```sh
docker compose up -d     # published on 5433 because 5432 is taken locally
```

### 2. Backend

Option A — uv (recommended):

```sh
cd backend
uv sync
uv run python -m scripts/seed_dev                      # roles + a dev admin
uv run python -m alembic upgrade head
uv run python -m uvicorn app.main:app --reload
```

Option B — plain venv + pip:

```sh
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python -m scripts/seed_dev
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

> Use `python -m alembic` / `python -m uvicorn` rather than the bare console scripts — on some
> Windows + uv combinations the generated shims exit with status 1 and no output.

Regenerate `requirements.txt` after changing dependencies:

```sh
uv export --no-hashes --no-emit-project --output-file requirements.txt
```

The seed script creates one development account per role and prints the shared password (default
`ChangeMe123!`):

| Email | Role |
|---|---|
| `admin@officehub.dev` | ADMIN |
| `support@officehub.dev` | IT_SUPPORT |
| `employee@officehub.dev` | EMPLOYEE |

Change them before this reaches any shared environment.

### 3. Frontend

```sh
cd frontend
pnpm install
pnpm dev
```

Open <http://localhost:5173>, sign in with the seeded admin, and you land on the dashboard shell.

Configuration lives in `backend/.env` and `frontend/.env` — copy from the `.env.example` files.

---

## Endpoints

| Method | URL | Purpose |
|---|---|---|
| GET | http://localhost:8000/ | service status (`{"status": "running"}`) |
| GET | http://localhost:8000/api/v1/health/live | liveness |
| GET | http://localhost:8000/api/v1/health/ready | readiness (503 if DB down) |
| POST | http://localhost:8000/api/v1/auth/login | set session cookie, returns the user |
| POST | http://localhost:8000/api/v1/auth/logout | revoke the session (204) |
| GET | http://localhost:8000/api/v1/auth/me | the signed-in user, 401 otherwise |
| GET | http://localhost:8000/api/v1/auth/csrf | CSRF token for the double-submit header |
| GET | http://localhost:8000/api/v1/users | list users — requires `users:read` (ADMIN) |
| GET | http://localhost:8000/api/v1/users/{user_id} | read a user — own account, or `users:read` |
| GET | http://localhost:8000/api/v1/rooms | list rooms — requires `rooms:read` |
| POST | http://localhost:8000/api/v1/rooms | create room — requires `rooms:create` |
| GET | http://localhost:8000/api/v1/rooms/{room_id} | room details |
| PATCH | http://localhost:8000/api/v1/rooms/{room_id} | update / disable — requires `rooms:update` |
| DELETE | http://localhost:8000/api/v1/rooms/{room_id} | delete room (204) — requires `rooms:delete` |
| GET | http://localhost:8000/api/v1/bookings | list bookings — own, or all for ADMIN |
| POST | http://localhost:8000/api/v1/bookings | book a room (201) — 409 on overlap |
| DELETE | http://localhost:8000/api/v1/bookings/{booking_id} | cancel a booking (204) |
| GET | http://localhost:8000/api/v1/rooms/{room_id}/availability | confirmed bookings for `?day=YYYY-MM-DD` |
| GET | http://localhost:8000/api/v1/audit-logs | audit trail — requires `audit:read` (ADMIN) |
| GET | http://localhost:8000/docs | OpenAPI docs |
| — | http://localhost:5173 | frontend dev server |

`POST`, `PUT`, `PATCH`, and `DELETE` require the CSRF header. The browser client handles this in
`frontend/src/lib/api/client.ts`; from the command line, read `csrf_token` out of the cookie jar and
send it as `X-CSRF-Token`.

---

## Checks

```sh
cd backend
uv run ruff check .
uv run python -m pytest
```

```sh
cd frontend
pnpm build     # tsc project build + production bundle
pnpm lint
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
