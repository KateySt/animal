---
name: rest-urls
description: >
  REST URL design checker for the Animal Shelter API. Validates URL structure,
  HTTP method → status code mapping, and router conventions. Run before adding any endpoint.
---

# /rest-urls — REST URL Conventions

## Rules

1. **Nouns, not verbs** — `POST /animals` not `POST /animals/create`
2. **Plural collections** — `/animals`, `/health-logs`, `/invoices`
3. **kebab-case segments** — `/health-logs` ✓ · `/healthLogs` ✗ · `/health_logs` ✗
4. **snake_case query params** — `?is_vaccinated=true&sort_by=name`
5. **Named path params** — `{animal_id}` not `{id}` (ambiguous in nested routes)

## Method → status code

| Method | Success | Notes |
|--------|---------|-------|
| POST | 201 | `status_code=status.HTTP_201_CREATED` |
| GET | 200 | default |
| PUT / PATCH | 200 | default |
| DELETE | 204 | `response_model=None` |

## Router file checklist

- [ ] `APIRouter()` with no prefix (prefix in `app/routers/__init__.py`)
- [ ] Every route has explicit `response_model=`
- [ ] POST → 201, DELETE → 204, no body on 204
- [ ] Path params named `{resource_id}` (e.g. `{animal_id}`, `{log_id}`)
- [ ] No DB logic — router calls service only
- [ ] Registered with plural kebab-case prefix + Title Case tag

## Non-CRUD actions

Use sub-resource nouns for state changes:
```
POST /animals/{animal_id}/adoption    # initiate adoption
DELETE /animals/{animal_id}/adoption  # cancel adoption
PATCH /animals/{animal_id}/status     # update status
```
Never: `POST /animals/{animal_id}/setStatus`

## Webhook rule (Stripe)

`POST /webhook` must be registered **before** `POST /{invoice_id}` — FastAPI path-param matching will swallow `/webhook` as a UUID otherwise (INV-5 in security-auditor).
