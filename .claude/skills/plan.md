---
name: plan
description: >
  Plan a new feature before writing any code. Fetches current library docs,
  identifies all files to touch, checks architecture rules, and produces a
  step-by-step implementation plan for approval. Use before any non-trivial
  feature: new model, new endpoint, auth changes, Stripe changes.
---

# /plan — Feature Implementation Planner

Invoke the `impl-planner` agent with the user's feature description.

## How to invoke

```
/plan <feature description>
```

Examples:
- `/plan add a notifications model with email and push channels`
- `/plan add rate limiting per user on the auth endpoints`
- `/plan add pagination to the animals list endpoint`
- `/plan upgrade fastapi to latest and fix breaking changes`

## What happens

1. `impl-planner` reads current project structure.
2. Spawns `lib-versions` in background to fetch current docs for relevant libraries.
3. Produces a concrete plan: files to create/modify, step-by-step with exact method signatures, migration command, test plan.
4. You review and approve — then implementation begins.

## When to use

- Any new model (triggers 8-step checklist from CLAUDE.md).
- Any change to auth flow, RBAC, or token handling.
- Any Stripe / invoice changes.
- Any time you're unsure which version of an API to use.

## Why it exists

Claude's training data has a cutoff. FastAPI, SQLAlchemy 2, Pydantic v2, and FastCRUD
all have frequent releases with breaking changes. Without fetching current docs first,
Claude may generate code using deprecated APIs (e.g. old SQLAlchemy 1.x `session.add` patterns,
Pydantic v1 validators, old FastAPI lifespan syntax). This skill prevents that.
