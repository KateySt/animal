---
name: fastapi-tests
description: >
  Run and audit the pytest suite for the Animal Shelter API against FastAPI +
  async SQLAlchemy testing best practices. Use when asked to run tests, write
  new tests, review test quality, diagnose flaky/failing tests, or check test
  coverage before a PR. Delegates deep audits to the fastapi-test-reviewer agent.
---

# FastAPI Test Runner & Best-Practices Checker — Animal Shelter API

## How to run the suite

Always use the project venv. From the repo root:

```bash
# Full suite (quiet, short traceback)
.venv/Scripts/python.exe -m pytest -q --tb=short

# One marker
.venv/Scripts/python.exe -m pytest -q -m unit
.venv/Scripts/python.exe -m pytest -q -m integration

# One file / one test
.venv/Scripts/python.exe -m pytest tests/integration/test_auth.py -q
.venv/Scripts/python.exe -m pytest "tests/integration/test_auth.py::test_login_success" -q

# Re-run only what failed last time, fail fast
.venv/Scripts/python.exe -m pytest --lf -x -q
```

Config lives in `[tool.pytest.ini_options]` in `pyproject.toml`:
`asyncio_mode = "auto"` (no need to mark every coroutine), `testpaths = ["tests"]`,
markers `unit` and `integration`. The test DB URL comes from `get_test_config()`.

## Test architecture in this repo (know it before touching tests)

- **`tests/conftest.py`** — session-scoped schema create/drop, per-test `db_session`
  wrapped in an outer transaction + savepoint that **rolls back after every test**
  (no data leaks between tests). Fixtures: `client`, `auth_client`,
  `superuser_client`, `read_only_client`, `user`, `bind_factories`.
- **`tests/integration/conftest.py`** — `autouse` binds factories to the rolled-back session.
- **`tests/factories.py`** — factory-boy factories. Bind to `db_session`, never open your own.
- Dependency overrides (`app.dependency_overrides`) inject the test session and a fake
  `Principal` — this is how auth is bypassed. Always clear overrides in the fixture teardown.

## FastAPI / async-SQLAlchemy testing best practices — the checklist

Run this checklist whenever writing or reviewing tests.

### Isolation & fixtures
- [ ] Every test runs inside the rolled-back `db_session` — **no manual commits** that escape the savepoint.
- [ ] Use the existing `client` / `auth_client` fixtures; don't build a fresh `AsyncClient` inline.
- [ ] Factories bound to the test session (`bind_factories`), never `AsyncSessionLocal()`.
- [ ] `app.dependency_overrides` is always cleared in teardown (leak → poisons later tests).
- [ ] No `scope="session"` on fixtures that hold data — only schema/engine may be session-scoped.

### Async correctness
- [ ] `httpx.AsyncClient` with `ASGITransport(app=app)` — never the sync `TestClient` for async endpoints.
- [ ] `await` on every client call and every `session.flush/execute`; no un-awaited coroutines.
- [ ] `LifespanManager(app)` wraps clients that need startup (Redis/cache) — matches existing fixtures.
- [ ] No `asyncio.run()` / `loop.run_until_complete()` inside tests — pytest-asyncio owns the loop.

### HTTP contract assertions
- [ ] Assert **exact status code** (`201` create, `204` delete, `401/403/404/409/422` errors), not just `< 400`.
- [ ] Assert the JSON **body/`response_model` shape**, not only the status.
- [ ] Error responses assert the `CustomError` mapping (e.g. `AlreadyExistsError` → `409`).
- [ ] `WWW-Authenticate` header asserted on `401` paths (project invariant #2).

### Coverage of behavior, not lines
- [ ] Happy path **and** the failure path for each endpoint (missing scope, not found, duplicate, bad body).
- [ ] RBAC: a `read_only_client` is rejected on write scopes; `superuser_client` bypasses; `auth_client` in-between.
- [ ] Auth flows: refresh **rotation** and **reuse-detection** (reused token revokes the chain) are tested.
- [ ] Webhook route tested **unauthenticated** with a signature check (invariant #3), not with auth bypass.
- [ ] Boundary inputs: empty lists, wrong enum values, oversized fields, null vs. missing.

### Determinism / no flakiness
- [ ] No dependence on test execution order or on rows from another test.
- [ ] Time/UUID/Stripe/Redis calls are stubbed or use fixed fakes — no real network, no `sleep`.
- [ ] No hard-coded PKs that collide across tests; use factories / `uuid4`.

### Anti-patterns to flag
- Asserting on `response.status_code < 400` instead of the precise code.
- `try/except: pass` swallowing an assertion.
- Sharing mutable state at module scope between tests.
- Testing framework internals (that FastAPI validates) instead of app behavior.
- Overusing `superuser_client` so real scope checks are never exercised.

## Workflow when invoked

1. **Run** the relevant scope first (`-m integration` or a single file) and read the output.
2. If **green**: run the best-practices checklist over the touched test files; report gaps as a
   short bullet list ordered by importance. Offer to add the missing cases.
3. If **red**: show the failing test names + the assertion/traceback tail. Diagnose whether it's a
   **product bug** (fix app code) or a **test bug** (fix the test). State which, then fix.
4. After any fix to app or test code, **re-run** the affected tests and confirm they pass before finishing.
5. For a deep, file-by-file audit, delegate to the `fastapi-test-reviewer` agent and summarize its verdict.

## Reporting format

```
### Test run
<command> → N passed / M failed / K skipped

### Failures (if any)
- test_name — one-line cause → fix applied (app bug | test bug)

### Best-practice gaps
- [file] missing failure-path test for <endpoint>
- [file] asserts status < 400 instead of exact 201

### Verdict
PASS / NEEDS-WORK + one sentence.
```
