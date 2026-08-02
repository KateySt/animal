---
name: plan
description: >
  Plan a new feature before writing any code. Fetches current library docs, identifies
  all files to touch, checks architecture rules, and produces an approved step-by-step
  plan. Use before any non-trivial feature: new model, auth changes, Stripe changes.
---

# /plan — Feature Planner

```
/plan <feature description>
```

Invokes `impl-planner` agent which:
1. Reads project structure + relevant existing files
2. Spawns `lib-versions` (background) to fetch current docs for affected libraries
3. Produces a concrete plan: files to create/modify, exact signatures, migration command, test plan
4. **You approve → then implementation begins**

## When to use

- Any new model (triggers 8-step checklist)
- Auth flow, RBAC, or token handling changes
- Stripe / invoice changes
- Any time you're unsure which library API version to use

## Why it exists

FastAPI, SQLAlchemy 2, Pydantic v2, and FastCRUD have frequent breaking changes. Without live docs, Claude may use deprecated APIs from training data. This skill prevents that.
