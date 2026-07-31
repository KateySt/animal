---
name: fastapi-tests
description: >
  Run and audit the pytest suite for the Animal Shelter API. Use when running tests,
  writing new tests, diagnosing failures, or checking coverage before a PR.
---

# /fastapi-tests — Test Runner & Checker

## Run

```bash
.venv/Scripts/python.exe -m pytest -q --tb=short          # full suite
.venv/Scripts/python.exe -m pytest -q -m integration      # integration only
.venv/Scripts/python.exe -m pytest tests/integration/test_auth.py -q  # one file
.venv/Scripts/python.exe -m pytest --lf -x -q             # last-failed, stop on first
```

Config in `pyproject.toml`: `asyncio_mode = "auto"`, markers `unit` / `integration`.

## Test infrastructure (read before touching tests)

- `tests/conftest.py` — session-scoped schema, per-test `db_session` with savepoint rollback. Fixtures: `client`, `auth_client`, `superuser_client`, `read_only_client`, `user`, `bind_factories`.
- `tests/factories.py` — factory-boy factories bound to `db_session`.
- Auth bypass via `app.dependency_overrides` (fake `Principal`). Always clear overrides in teardown.

## Checklist

### Isolation
- [ ] No manual `commit()` escaping the savepoint
- [ ] Factories use `db_session`, never `AsyncSessionLocal()`
- [ ] `dependency_overrides` cleared in teardown

### Async correctness
- [ ] `httpx.AsyncClient` + `ASGITransport(app=app)` — not sync `TestClient`
- [ ] Every client call and session op is awaited
- [ ] No `asyncio.run()` inside tests

### HTTP contracts
- [ ] Exact status codes (`201`, `204`, `401`, `403`, `404`, `409`, `422`) — not `< 400`
- [ ] Response body shape asserted, not just status
- [ ] `WWW-Authenticate` header asserted on 401 (project invariant)
- [ ] `CustomError` → status mapping exercised

### Coverage
- [ ] Happy path + failure path per endpoint (missing scope, not found, duplicate, bad body)
- [ ] RBAC: `read_only_client` rejected on writes; `superuser_client` bypass; `auth_client` scoped
- [ ] Auth: refresh rotation + reuse-detection (revoked token revokes chain)
- [ ] Webhook tested **unauthenticated** with signature verification
- [ ] Boundary inputs: empty lists, invalid enums, null vs. missing

### Flakiness
- [ ] No cross-test ordering dependence
- [ ] Stripe / Redis / time / UUID stubbed — no real network, no `sleep`

## Workflow

1. Run suite → read output
2. **Green**: run checklist on touched test files, report gaps ordered by impact
3. **Red**: show failing test + traceback tail, diagnose (product bug vs. test bug), fix, re-run
4. Deep audit → delegate to `fastapi-test-reviewer` agent

## Report format

```
### Test run
<cmd> → N passed / M failed / K skipped

### Failures
- test_name — cause → fix (app bug | test bug)

### Gaps
- [file] missing failure-path for <endpoint>

### Verdict
PASS / NEEDS-WORK — one sentence
```
