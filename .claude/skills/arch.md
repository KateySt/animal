---
name: arch
description: >
  Clean Architecture layer checker for the Animal Shelter API. Detects dependency
  direction violations, layer leaks, and missing transaction scope. Run before any PR.
---

# /arch — Architecture Checker

Layer order: **Models ← FastCRUD ← Services ← Routers**. Schemas never import ORM.

## Run these greps first

```bash
grep -rn "from app.db.models" app/schemas/        # schema → model (violation)
grep -rn "from app.schemas" app/db/models/         # model → schema (violation)
grep -rn "from app.db.models\|from app.repo\|_crud" app/routers/  # router bypasses service
grep -rn "raise HTTPException" app/services/       # bare HTTP error in service
```

## Layer rules

| Layer | May import | Must NOT import |
|-------|-----------|----------------|
| Models | stdlib only | schemas, services, routers |
| Services | models, FastCRUD, schemas | routers, other services' sessions |
| Routers | services, schemas, dependencies | models, `*_crud`, raw sessions |
| Schemas | stdlib, pydantic | ORM models, SQLAlchemy types |

## Key violations to flag

**Schema constructs ORM**: `to_animal(self) -> Animal` method on a Pydantic class → move mapping to service.

**Multi-write without transaction**:
```python
# WRONG — partial failure orphans the animal
animal = await animal_crud.create(...)
await health_log_crud.create(...)  # if this fails, animal row is orphaned

# CORRECT
async with session.begin():
    animal = await animal_crud.create(...)
    await health_log_crud.create(...)
```

**Router imports crud**: `from app.db.models import animal_crud` in a router → add service method.

**Service returns ORM instance** without mapping to response schema → always return Pydantic model from service (or let router map via `response_model=`).

## Verdict format

```
✅ PASS  — all layers clean
⚠ WARN  — [file:line] description (non-blocking)
✗ BLOCK — [file:line] violation — do not merge
```
