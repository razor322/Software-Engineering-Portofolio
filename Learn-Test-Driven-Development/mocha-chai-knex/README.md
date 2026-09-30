# mocha-chai-knex

> **A RESTful API built test-first — one failing test at a time.**

A TV-shows REST API written with **Node, Express, Knex, and PostgreSQL**, developed entirely with
**Test-Driven Development**: every route in this project exists because a test demanded it.

This is a learning project from the [**Learn Test-Driven Development**](../README.md) track of my
[Software Engineering Portfolio](../../README.md).

---

## Table of Contents

1. [What This Project Is](#-what-this-project-is)
2. [The Red/Green/Refactor Cycle](#-redgreenrefactor-cycle)
3. [Test Suite](#-test-suite)
4. [Architecture](#-architecture)
5. [Key Design Points](#-key-design-points)
6. [What I Learned](#-what-i-learned)
7. [What Is Not Handled Yet](#-what-is-not-handled-yet)
8. [Technology Stack](#-technology-stack)
9. [Project Structure](#-project-structure)
10. [Getting Started](#-getting-started)
11. [API Endpoints](#-api-endpoints)
12. [Sources & Credits](#-sources--credits)

---

## 🎯 What This Project Is

A deliberately small API — 5 routes over a single `shows` table — chosen because it is small enough
that the *process* stays visible. The point was never the CRUD app; the point was learning how to let
tests drive every decision:

```text
     🔴 RED               🟢 GREEN              ♻️ REFACTOR
  ─────────────        ─────────────        ────────────────
  Write a test         Write the code       Clean up the code
  that fails           to make it pass      keep the tests green
        │                    │                     │
        ▼                    ▼                     ▼
  "expected 200,       "1 passing"          Better design,
   got 404"                                  same behavior
```

Each of the 5 routes was built in that order. No route was written before a failing test described it.

---

## 🔴🟢♻️ Red/Green/Refactor Cycle

The actual loop followed for every route:

### 1. 🔴 Red — the test describes the contract

The first test asserted on a route that did not exist yet, and failed for exactly that reason:

```js
chai.request(server)
  .get('/api/v1/shows')
  .end(function(err, res) {
    res.should.have.status(200);
    res.should.be.json;
    res.body.should.be.a('array');
    res.body.length.should.equal(4);
    // ...
    done();
  });
```

```text
API Routes
  GET /api/v1/shows
    1) should return all shows

  0 passing
  1 failing
     Uncaught AssertionError: expected 'text/html; charset=utf-8'
     to include 'application/json'
```

**Why this matters:** a test that has never failed has never proven it can detect anything.
The failure was *meaningful* — plain text was returned where JSON was expected — which confirmed
the test was actually exercising the route.

### 2. 🟢 Green — the minimum code to pass

Only then did the query and route get written:

```js
// db/queries.js
function getAll() {
  return Shows().select();
}

// routes/index.js
router.get('/shows', function(req, res, next) {
  queries.getAll()
    .then(function(shows) {
      res.status(200).json(shows);
    })
    .catch(function(error) {
      next(error);
    });
});
```

```text
API Routes
  GET /api/v1/shows
    ✓ should return all shows (128ms)

1 passing
```

### 3. ♻️ Refactor — improve with the safety net in place

With the test green, the design was improved: database state was made reproducible with
`beforeEach` / `afterEach` hooks, and the `PUT` route was hardened after a test revealed that
the `id` field could be overwritten.

**The cycle repeated 6 times.** The final result:

```text
  API Routes
    Get all shows
      ✔ should get all shows
    GET /api/v1/shows/:id
      ✔ should return a single show
    POST /api/v1/shows
      ✔ should add a show
    PUT /api/v1/shows/:id
      ✔ should update a show
      ✔ should NOT update a show if the id field is part of the request
    DELETE /api/v1/shows/:id
      ✔ should delete a show

  6 passing (425ms)
```

---

## ✅ Test Suite

**6 tests, 6 passing.** Integration tests hit the real Express app over HTTP and assert against a
real PostgreSQL test database — no mocks.

| Test | Asserts |
|---|---|
| `GET /api/v1/shows` | Status 200, JSON content type, array of 4 seeded shows, exact field values of the first item |
| `GET /api/v1/shows/:id` | Status 200, single object returned with the correct field values |
| `POST /api/v1/shows` | Status 200, created show returned with the submitted values |
| `PUT /api/v1/shows/:id` | Status 200, updated values returned with unchanged fields intact |
| `PUT` with `id` in body | Status **422**, error message returned, update rejected |
| `DELETE /api/v1/shows/:id` | Deleted show returned, then a follow-up `GET` confirms the list shrank to 3 items |

### Test isolation

Tests must never depend on each other or on leftover data. Every test starts from an identical
database state:

```js
beforeEach(function(done) {
  knex.migrate.rollback()
    .then(function() {
      knex.migrate.latest()
        .then(function() {
          return knex.seed.run()
            .then(function() { done(); });
        });
    });
});

afterEach(function(done) {
  knex.migrate.rollback()
    .then(function() { done(); });
});
```

```text
rollback  →  drop everything from the previous run
migrate   →  rebuild the schema from migration files
seed      →  insert the same 4 known rows
   ↓
test runs against a guaranteed-known state
```

**Rollback happens *before* each test, not only after.** If a test throws an error, `afterEach` is
never reached — so rolling back up front guarantees the next test still starts clean.

---

## 🏗️ Architecture

```text
┌──────────────────────────────────────────────────────────┐
│                      Mocha + Chai                        │
│                                                          │
│   chai.request(server).get('/api/v1/shows')              │
└──────────────────────────┬───────────────────────────────┘
                           │ HTTP
                           ▼
┌──────────────────────────────────────────────────────────┐
│                    Express app (app.js)                  │
│                                                          │
│   routes/index.js ──── route handlers                    │
│          │                                               │
│          ▼                                               │
│   db/queries.js ────── all database access               │
│          │                                               │
│          ▼                                               │
│   db/knex.js ───────── picks env config                  │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                       knexfile.js                        │
│                                                          │
│   test ─────▶ mocha_chai_tv_shows_test                   │
│   development ▶ mocha_chai_tv_shows                      │
│   production ─▶ DATABASE_URL                             │
└──────────────────────────────────────────────────────────┘
```

**Why this shape:** routes stay thin (HTTP concerns only), queries are centralized (SQL concerns only),
and the environment decides which database is used — so the exact same code path is exercised in
tests and in development.

---

## 🔑 Key Design Points

**A separate test database, selected by `NODE_ENV`**

```js
// db/knex.js
var environment = process.env.NODE_ENV || 'development';
var config = require('../knexfile.js')[environment];

module.exports = require('knex')(config);
```

The test file sets `process.env.NODE_ENV = 'test'` as its very first line — before `app` is required —
so tests can rollback, migrate, and seed freely without ever touching development data.

**Logging is silenced during tests**

```js
if (process.env.NODE_ENV !== 'test') {
  app.use(logger('dev'));
}
```

Otherwise every HTTP request would flood the test output and make failures hard to read.

**The `id` field is immutable**

A test proved that sending `id` in a `PUT` body silently reassigned the primary key.
The route now rejects it:

```js
router.put('/shows/:id', function(req, res, next) {
  if (req.body.hasOwnProperty('id')) {
    return res.status(422).json({
      error: 'You cannot update the id field'
    });
  }
  // ...
});
```

**DELETE returns the deleted resource**

Knex's `.del()` only reports *how many* rows were affected, so the record is fetched first
and returned after deletion — giving the client the deleted object instead of a count.

**Queries are centralized**

Every route goes through `db/queries.js`. No SQL is written inside route handlers, which keeps
the HTTP layer testable and the database layer reusable.

---

## 🧠 What I Learned

- **Write the test first — genuinely.** Watching a test fail for the right reason is the only proof
  that the test verifies anything. A test written after the code tends to verify whatever the code
  happens to do.
- **`done()` and async tests.** Integration tests are asynchronous; Mocha needs the `done()` callback
  to know when a test has actually finished.
- **Test isolation is a database problem.** Reproducible state comes from `migrate.rollback()` →
  `migrate.latest()` → `seed.run()` around every test, not from hoping the data is still there.
- **Failures are the deliverable.** The most valuable test in this project was the one that exposed
  the mutable `id` field — it found a real bug that a passing suite would have hidden.
- **Test at the HTTP boundary.** Asserting on status codes, content types, and response bodies catches
  integration problems that unit tests on query functions would miss entirely.
- **Green tests are permission to refactor.** Once the suite passed, restructuring the routes and
  queries became low-risk instead of frightening.
- **The suite documents behavior.** Reading the test file tells you what the API does more precisely
  than any prose description.
- **A green suite can still hide broken behavior.** Every test here covers the *happy path*; not one
  of them asserts what happens on invalid input. All 6 tests pass while the API still answers errors
  with HTML instead of JSON — proof that "tests are green" and "the API is correct" are different claims.

---

## 🚧 What Is Not Handled Yet

**The project is honest about its limits.** The suite is green, but green does not mean complete.

> So there you have it: A test-first approach to developing a RESTful API. Are we done? Not quite since
> we are not handling or testing for all possible errors.
>
> For example, what would happen if we tried to POST an item without all the required fields? Or if we
> tried to delete an item that isn't in the database? Sure the `catch()` methods will handle these, but
> they are simply passing the request to the built-in error handlers. We should handle these better in
> the routes and throw back appropriate error messages and status codes.
>
> — Michael Herman, [*Test Driven Development with Node, Postgres, and Knex*](https://mherman.org/blog/test-driven-development-with-node/)

This is the correct place for this project to stop — and the correct place for the next iteration to begin.

### Unhandled cases I can now identify

| Case | Current behavior | Desired behavior |
|---|---|---|
| `POST` missing required fields | Database `NOT NULL` violation → generic **500** | **400** with which fields are missing |
| `POST` duplicate `name` | Unique constraint violation → generic **500** | **409 Conflict** with a clear message |
| `GET /shows/:id` for a missing id | Returns **200** with an empty body | **404 Not Found** |
| `PUT` on a missing id | Update affects 0 rows, `getSingle` returns empty | **404 Not Found** |
| `DELETE` on a missing id | Returns **200** with an empty body | **404 Not Found** |
| `GET /shows/abc` (non-numeric id) | `parseInt` yields `NaN` → confusing query | **400 Bad Request** |
| Invalid `rating` (non-integer, negative, > 5) | Stored as-is | **422** with a validation message |

### The error responses are HTML, not JSON

There is a second, deeper problem: the error handlers in [`app.js`](./app.js) still render **Pug templates**,
so any error returns an HTML page — not a JSON body:

```js
// app.js — current state
if (app.get('env') === 'development') {
  app.use(function (err, req, res, next) {
    res.status(err.status || 500);
    res.render('error', { message: err.message, error: err });
  });
}
```

A REST API should answer every request with JSON, including failures — a client parsing `res.json()`
will break on an HTML error page. This is a concrete, visible gap between the code and the
article's own recommendation, which explicitly calls for switching these handlers to `res.json(...)`.

**Why these are still open:** the `catch()` blocks currently just forward errors to the built-in
Express error handlers, which return generic 500 responses (as HTML). The `catch()` blocks are doing
their job — but they are not *handling* anything. Properly fixing this means:

1. **Write a failing test for each case first** — the error behavior is a contract and deserves the
   same Red/Green/Refactor treatment as the happy paths.
2. **Return JSON from the error handlers** — replace `res.render('error', ...)` with `res.json(...)`
   so failures speak the same language as successes.
3. **Validate in the route** and return appropriate status codes (**400 / 404 / 409 / 422**) with
   meaningful JSON error messages.
4. **Return a consistent error envelope** so clients get a predictable shape for every failure.
5. **Keep `next(error)` as the last resort** — for genuinely unexpected failures, not as the default
   path for predictable ones.

This is exactly the "Prove It" discipline of the portfolio: knowing the difference between
*tests passing* and *behavior being correct*.

---

## 🛠️ Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Runtime | Node.js | |
| Web framework | **Express 5** | Article used Express 4 |
| Query builder | **Knex 3** | Article used Knex 0.10 |
| Database | **PostgreSQL** | `pg` driver |
| Test runner | **Mocha 10** | `npm test` |
| Assertions | **Chai 4** (should style) | |
| HTTP assertions | **Chai-HTTP 4** | Integration requests against the real app |
| View engine | Pug | From the Express generator boilerplate |

### Modernization notes

This guide was written in 2016, so the code was adapted to run on current versions:

- **Express 5 / body-parser 2** — updated middleware and router behavior.
- **Knex 3** — `.insert(show, 'id')` returns differently than it did in Knex 0.10, so the `POST`
  route normalizes the returned id before re-querying:

  ```js
  var id = showID[0] && showID[0].id ? showID[0].id : showID[0] || showID;
  ```

- **`.returning('*')`** was added to `update()` and `deleteItem()` — supported by modern PostgreSQL
  and Knex, and a cleaner way to return the affected row.
- **Chai 4** instead of Chai 3, and Mocha 10 instead of Mocha 2.

Running the older pinned versions from the article is no longer practical; the Red/Green/Refactor
*process* is what transferred, and adapting the code was itself part of the learning.

---

## 📁 Project Structure

```text
mocha-chai-knex/
│
├── bin/
│   └── www                      # server bootstrap
│
├── db/
│   ├── migrations/
│   │   └── ..._create_tv_shows_table.js   # up() creates shows, down() drops it
│   ├── seeds/
│   │   ├── development/shows_seed.js      # 4 shows for development
│   │   └── test/shows_seed.js             # identical 4 shows for tests
│   ├── knex.js                  # environment selection
│   └── queries.js               # all database queries
│
├── routes/
│   ├── index.js                 # the 5 API routes
│   └── users.js                 # generator boilerplate, unused
│
├── test/
│   └── route.spec.js            # the entire test suite
│
├── views/                       # pug templates (boilerplate)
├── app.js                       # Express app — exported for testing
├── knexfile.js                  # test / development / production configs
└── package.json                 # `npm start`, `npm test`
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** and npm
- **PostgreSQL** running locally

### 1. Install dependencies

```sh
npm install
```

### 2. Create the databases

```sh
psql -U postgres
```

```sql
CREATE DATABASE mocha_chai_tv_shows;
CREATE DATABASE mocha_chai_tv_shows_test;
\q
```

### 3. Configure the connection

Update the credentials in [`knexfile.js`](./knexfile.js) to match your local PostgreSQL setup:

```js
connection: 'postgres://<user>:<password>@localhost:5432/mocha_chai_tv_shows_test'
```

### 4. Run migrations and seeds

```sh
npx knex migrate:latest --env development
npx knex seed:run --env development
```

> The test database does not need manual migration or seeding — the `beforeEach` hook handles
> rollback, migration, and seeding automatically on every test run.

### 5. Run the tests

```sh
npm test
```

Expected output:

```text
  API Routes
    Get all shows
      ✔ should get all shows
    GET /api/v1/shows/:id
      ✔ should return a single show
    POST /api/v1/shows
      ✔ should add a show
    PUT /api/v1/shows/:id
      ✔ should update a show
      ✔ should NOT update a show if the id field is part of the request
    DELETE /api/v1/shows/:id
      ✔ should delete a show

  6 passing
```

### 6. Run the server

```sh
npm start
```

Then browse to <http://localhost:3000/api/v1/shows>.

---

## 🌐 API Endpoints

All routes are prefixed with `/api/v1`.

| Method | Endpoint | Description | Status |
|---|---|---|---|
| `GET` | `/api/v1/shows` | List all shows | 200 |
| `GET` | `/api/v1/shows/:id` | Get a single show | 200 |
| `POST` | `/api/v1/shows` | Create a show | 200 |
| `PUT` | `/api/v1/shows/:id` | Update a show | 200 · 422 if `id` is in the body |
| `DELETE` | `/api/v1/shows/:id` | Delete a show and return it | 200 |

### Show resource

```json
{
  "id": 1,
  "name": "Suits",
  "channel": "USA Network",
  "genre": "Drama",
  "rating": 3,
  "explicit": false
}
```

### Example

```sh
curl http://localhost:3000/api/v1/shows
```

```sh
curl -X POST http://localhost:3000/api/v1/shows \
  -H "Content-Type: application/json" \
  -d '{"name":"Family Guy","channel":"Fox","genre":"Comedy","rating":4,"explicit":true}'
```

---

## 📚 Sources & Credits

Built by following and modernizing a guided learning resource:

- **Article** — [*Test Driven Development with Node, Postgres, and Knex (Red/Green/Refactor)*](https://mherman.org/blog/test-driven-development-with-node/) by [Michael Herman](https://mherman.org/).
- **Reference implementation** — [mjhea0/mocha-chai-knex](https://github.com/mjhea0/mocha-chai-knex).
- **Edits credited by the author** — [Bradley Bouley](https://www.linkedin.com/in/bbouley/).

---

## 🧭 Guiding Principle

> **Red. Green. Refactor.**
>
> The tests are not there to prove the code works —
> they are there to tell you what to build next.

---

## 📬 Navigate

- Back to the **[Learn Test-Driven Development](../README.md)** track.
- Back to the **[portfolio root](../../README.md)**.
