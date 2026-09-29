# 🧭 Software Engineering Portfolio

> **A learning journey from "it works on my machine" to production-grade systems.**

This repository is the **umbrella of my software engineering portfolio** — a collection of projects
built with one purpose: to learn how real software is engineered **end to end**, not just written.

Every project here starts simple and grows toward production: designed, secured, tested,
observed, deployed, backed up, and improved only when a real problem demands it.

---

## 🎯 Why This Portfolio Exists

Most learning stops at the demo: a CRUD app runs locally, and that's it.

Real engineering begins where the demo ends:

```text
It runs on my machine
        ↓
It runs on someone else's machine
        ↓
It survives failures
        ↓
It can be deployed, monitored, and rolled back
        ↓
It can be trusted
```

This portfolio is my deliberate practice at crossing that gap. Each project answers a set of questions:

| Question | What I practice |
|---|---|
| **How is it built?** | Architecture, structure, patterns, technology choices |
| **How is it protected?** | Authentication, authorization, security by design |
| **How do I know it works?** | Testing, linting, type safety, CI pipelines |
| **How is it observed?** | Logs, metrics, traces, request correlation, error tracking |
| **How does it survive?** | Backups, recovery, rollbacks, incident response |
| **How does it grow?** | Measuring first, optimizing second, scaling only when proven necessary |

The goal is understanding **why** a technology exists — not collecting technologies for a résumé.

---

## 🗺️ The Journey

```text
   Write Code
       │
       ▼
   Structure It          ← clean architecture, modular design
       │
       ▼
   Secure It             ← auth, RBAC, validation, hardening
       │
       ▼
   Prove It             ← tests, lint, type checks, CI
       │
       ▼
   Observe It           ← logs, metrics, dashboards, error tracking
       │
       ▼
   Operate It           ← deployments, backups, recovery, runbooks
       │
       ▼
   Improve It           ← measure first, then optimize
       │
       ▼
   Scale It             ← only after the monolith is understood
```

Order matters. Correctness → security → testability → observability → recoverability → deployability —
**before** performance and scalability.

---

## 📂 Projects

| Project | Description | Status |
|---|---|---|
| [**Learn Backend dev to prod**](./Learn%20Backend%20dev%20to%20prod) | **OfficeHub** — a production-oriented room booking & IT ticketing platform (FastAPI + React + PostgreSQL). A learning laboratory for the full backend engineering journey: configuration, migrations, security, observability, CI/CD, and operations. | 🚧 In progress |

New projects will be added here as the portfolio grows — each one targeting a different corner
of software engineering.

---

## 🧱 Learning Pillars

```text
┌────────────────────────────────────────────────────────────┐
│                  SOFTWARE ENGINEERING                      │
├──────────────┬──────────────┬──────────────┬───────────────┤
│   Backend    │   Frontend   │    Data      │   DevOps      │
│  APIs, auth, │  React, TS,  │ PostgreSQL,  │ Docker, CI/CD,│
│  services,   │  routing,    │ migrations,  │ deployment,   │
│  architecture│  server state│  integrity   │ recovery      │
├──────────────┼──────────────┼──────────────┼───────────────┤
│  Security    │   Testing    │ Observability│  Operations   │
│  hardening,  │  unit, e2e,  │ logs, metrics│  backups,     │
│  RBAC, CSRF, │  regression, │ traces, error│  monitoring,  │
│  secrets     │  CI gates    │ tracking     │  incidents    │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

---

## 🛠️ Repository Standards

This portfolio itself is treated as an engineering artifact:

- **Conventional Commits** — enforced by [commitlint](./commitlint.config.cjs) so history stays readable and machine-parseable.
- **Husky hooks** — commit messages are validated automatically before every commit.
- **standard-version** — automated semantic versioning and changelogs (`release`, `release:minor`, `release:major`, `release:patch`).

```sh
npm run release        # patch bump + changelog + commit
npm run release:minor  # minor bump
npm run release:major  # major bump
```

---

## 📁 Structure

```text
Software-Engineering-Portfolio/
│
├── Learn Backend dev to prod/     # OfficeHub — backend to production
│
├── commitlint.config.cjs          # conventional commit rules
├── package.json                   # release tooling
├── .husky/                        # git hooks
└── README.md                      # you are here
```

Each project folder contains its own README with its specific architecture,
features, and setup instructions.

---

## 🧭 Guiding Principle

> **Build simple. Understand deeply. Improve only when proven necessary.**
>
> The purpose of this portfolio is to learn the engineering journey —
> not to skip directly to the final architecture.

---

## 📬 Navigate

- Start with **[Learn Backend dev to prod](./Learn%20Backend%20dev%20to%20prod)** → its [README](./Learn%20Backend%20dev%20to%20prod/README.md) explains OfficeHub's architecture, implemented features, and key design decisions.
