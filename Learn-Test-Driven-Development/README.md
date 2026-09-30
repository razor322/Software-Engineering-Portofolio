# 🧪 Learn Test-Driven Development

> **Write the test first. Watch it fail. Make it pass. Then make it better.**

This folder is a **learning track** inside my [Software Engineering Portfolio](../README.md) —
dedicated to one discipline: **proving that code works before claiming it works.**

Testing is not a checkbox at the end of a project. It is a design tool, a specification,
and the safety net that makes refactoring and production changes possible.
This track is where I practice it deliberately, starting with the most fundamental form:
**Test-Driven Development (TDD)**.

---

## 🎯 Why This Track Exists

In the portfolio journey, this track lives at the **"Prove It"** stage:

```text
   Write Code
       │
       ▼
   Structure It
       │
       ▼
   Secure It
       │
       ▼
   Prove It          ◀── you are here (tests, lint, type checks, CI)
       │
       ▼
   Observe It
       │
       ▼
   Operate It
       │
       ▼
   Improve It
```

You cannot observe, deploy, or scale a system you cannot verify.
TDD is the first, smallest, and most repeatable version of verification:
a tight loop where every line of production code exists because a test demanded it.

---

## 🔴🟢♻️ The Loop I Practice

Every project in this track follows the same cycle:

```text
        ┌──────────────────────────────────────────┐
        │                                          │
        ▼                                          │
   🔴 RED ──────────▶ 🟢 GREEN ──────────▶ ♻️ REFACTOR
   Write a test       Write the minimum     Clean up the
   that fails         code to pass it       code, keep tests
        │                    │              green
        │                    │                    │
        ▼                    ▼                    ▼
   Test defines        Code is proven        Design improves
   the contract        to satisfy it         without fear
```

| Phase | Rule I follow |
|---|---|
| 🔴 **Red** | The test must fail **for the right reason** — a failing test proves the test can actually detect failure |
| 🟢 **Green** | Write only enough code to pass. No speculative features |
| ♻️ **Refactor** | Improve structure with the tests as a safety net — behavior must not change |

---

## 🧱 Principles This Track Teaches

- **Tests are the specification** — the test describes the expected behavior before any implementation exists.
- **Fail first, always** — a test that has never failed has never proven anything.
- **Isolation** — each test starts from a known, reproducible database state, never from leftover data.
- **The suite is a contract** — green tests are permission to refactor, change, and deploy.
- **Coverage is a question, not a number** — "what happens when this goes wrong?" matters more than a percentage.

---

## 📂 Projects

| Project | Description | Tests | Status |
|---|---|---|---|
| [**mocha-chai-knex**](./mocha-chai-knex) | A RESTful TV-shows API built test-first with **Node + Express + Knex + PostgreSQL**, tested with **Mocha, Chai, and Chai-HTTP**. Full Red/Green/Refactor cycle across 5 routes. | 6 passing | ✅ Complete |

New TDD exercises will be added here as the track grows — each one targeting a different
layer of the stack (unit, integration, and end-to-end).

---

## 🧠 Skills Practiced in This Track

```text
┌────────────────────────────────────────────────────────────┐
│                    TEST-DRIVEN DEVELOPMENT                 │
├──────────────┬──────────────┬──────────────┬───────────────┤
│   The Cycle  │   Tooling    │    Data      │  Test Design  │
│  red/green/  │  Mocha, Chai │  migrations, │  integration, │
│  refactor,   │  Chai-HTTP,  │  seeds, test │  isolation,   │
│  fail-first  │  npm scripts │  environments│  status codes │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

Concretely, after this track I can:

- Drive an API's design from failing tests instead of writing tests after the fact.
- Set up **Mocha + Chai + Chai-HTTP** for integration tests against a real Express app.
- Separate **test / development / production** environments (Knex configs, database per environment).
- Keep tests isolated with `beforeEach` / `afterEach` using migration rollback, migrate, and re-seed.
- Assert on HTTP contracts: status codes, content type, response shape, and values.
- Recognize what is still **not** tested — and treat that as the next test to write.

---

## 📚 Sources & Credits

The exercises in this track are built from guided learning material, then modernized and adapted:

- **Michael Herman** — [*Test Driven Development with Node, Postgres, and Knex (Red/Green/Refactor)*](https://mherman.org/blog/test-driven-development-with-node/) — the original guide this track follows.
- **Reference repository** — [mjhea0/mocha-chai-knex](https://github.com/mjhea0/mocha-chai-knex).
- **Modernization notes** — the article is from 2016, so the implementation here runs on current versions (Express 5, Knex 3, Chai 4, Mocha 10) and documents the differences encountered along the way.

---

## 🧭 Guiding Principle

> **A test that has never failed has never proven anything.**
>
> Green tests are not decoration — they are the permission to change code without fear.

---

## 📬 Navigate

- Start with **[mocha-chai-knex](./mocha-chai-knex)** → its [README](./mocha-chai-knex/README.md) walks through the full Red/Green/Refactor cycle, the test setup, and what is deliberately left untested.
- Back to the **[portfolio root](../README.md)** → the full engineering journey this track belongs to.
