---
name: arch
description: >
  Clean Architecture layer checker for the Animal Shelter API. Run before any
  PR to detect dependency rule violations, layer leaks, and mapping
  responsibilities in the wrong place. Use when adding models, schemas,
  services, or repos — or when asked to audit architecture.
---

# Clean Architecture Checker — Animal Shelter API

## Dependency Rule (non-negotiable)

Dependencies flow **inward only**. Outer layers know about inner layers; inner layers must NOT know about outer layers.

```
Routers  →  Services  →  Repositories  →  Models (ORM)
    ↓            ↓              ↓
  Schemas     Schemas        Schemas
```

- **Models** (`app/db/models/`): pure SQLAlchemy. No Pydantic, no schemas, no routers.
- **Repositories** (`app/repo/`): accept/return ORM model instances only. No schemas.
- **Services** (`app/services/`): orchestrate repos, own transactions, map between schemas and models.
- **Schemas** (`app/schemas/`): pure Pydantic. No ORM imports, no SQLAlchemy types.
- **Routers** (`app/routers/`): parse HTTP → call service → return schema. No repos, no models, no ORM.

---

## Layer Violation Checklist

Run each check mentally (or via grep) on every file you touch.

### Schema layer (`app/schemas/`)

| Check | Violation signal | Fix |
|-------|-----------------|-----|
| Schema imports ORM model | `from app.db.models.X import X` inside a schema file | Move mapping to service |
| Schema constructs ORM instance | `def to_animal(self) -> Animal:` method on a Pydantic class | Extract to `AnimalMapper` in service layer |
| Schema imports SQLAlchemy types | `from sqlalchemy import ...` | Never — schemas are pure Pydantic |

**Current known violation** (`app/schemas/animal.py`):
```python
# VIOLATION — schema imports ORM and constructs instances
from app.db.models.animal import Animal
from app.db.models.health_log import HealthLog

class AnimalCreate(BaseModel):
    def to_animal(self) -> Animal: ...        # schema → ORM: wrong direction
    def to_health_logs(...) -> list[HealthLog]: ...  # same violation
```

Correct pattern — mapping belongs in the service:
```python
# app/services/animal_service.py
class AnimalAdmissionService:
    async def register_animal_with_health_history(self, payload: AnimalCreate) -> AnimalResponse:
        animal = Animal(
            name=payload.name,
            gender=payload.gender,
            birth_date=payload.birth_date,
            caretaker_notes=payload.caretaker_notes,
        )
        async with self._session.begin():
            created_animal = await self._animal_repo.create(animal)
            for log_payload in payload.health_logs:
                await self._health_log_repo.create(
                    HealthLog(animal_id=created_animal.id, **log_payload.model_dump())
                )
        return await self._animal_repo.get_by_id(created_animal.id)
```

---

### Repository layer (`app/repo/`)

| Check | Violation signal | Fix |
|-------|-----------------|-----|
| Repo imports schema | `from app.schemas import ...` | Accept/return only model instances |
| Repo contains business logic | `if animal.is_vaccinated:` conditions | Move to service |
| Repo calls another repo | `self._health_log_repo.create(...)` | Repos are independent; compose in service |
| Missing transaction ownership | `flush()` without `begin()` in caller | Transaction scope belongs in service, not repo |

### Service layer (`app/services/`)

| Check | Violation signal | Fix |
|-------|-----------------|-----|
| Service accesses `session` directly for raw SQL | `await self._session.execute(text(...))` | Extract to repo method |
| Multi-repo writes without transaction | two `await repo.create()` calls with no `begin()` | Wrap in `async with session.begin()` |
| Service returns ORM instance | `return animal` where return type is `Animal` (ORM) | Map to response schema before returning, OR let router map it |
| Business logic in `__init__` | validation/defaults set in service constructor | Move to schema validators or model defaults |

**Current known violation** (`app/services/animal_service.py:20-23`):
```python
# VIOLATION — two writes without transaction scope
async def create_animal_with_initial_health_log(self, payload: AnimalCreate) -> Animal:
    animal = await self._animal_repo.create(payload.to_animal())   # flush 1
    for health_log in payload.to_health_logs(animal.id):
        await self._health_log_repo.create(health_log)             # flush 2 — if this fails, animal is orphaned
    return await self.get_animal_by_id(animal.id)
```

Correct pattern:
```python
async def register_animal_with_health_history(self, payload: AnimalCreate) -> Animal:
    animal = Animal(name=payload.name, gender=payload.gender, ...)
    logs = [HealthLog(animal_id=...) for ...]
    async with self._session.begin():          # atomic — both succeed or both roll back
        created = await self._animal_repo.create(animal)
        for log in logs:
            await self._health_log_repo.create(log)
    return await self.get_animal_by_id(created.id)
```

### Router layer (`app/routers/`)

| Check | Violation signal | Fix |
|-------|-----------------|-----|
| Router imports repo | `from app.repo import AnimalRepository` | Routers only depend on services |
| Router imports ORM model | `from app.db.models.animal import Animal` | Return schemas only |
| Router contains `if/else` business logic | conditionals beyond "call service, return result" | Move to service |
| Router creates DB session manually | `session = AsyncSessionLocal()` | Use `Depends(get_db_session)` via service factory |
| Missing `response_model=` | `@router.get("/")` without response_model | Always explicit — prevents ORM object leakage |

### Model layer (`app/db/models/`)

| Check | Violation signal | Fix |
|-------|-----------------|-----|
| Model imports schema | `from app.schemas import ...` | Models are innermost — no outward imports |
| Model contains HTTP/API logic | `def to_json(self):` or `def to_response(self):` | Move to schema or mapper |
| Property computes from lazy-loaded relation | `@property` accessing a `lazy="raise"` relation | Will raise outside session; move to service |
| Missing `ondelete=` on FK | `ForeignKey("animals.id")` without `ondelete` | Add `ondelete="CASCADE"` or `"SET NULL"` |

---

## Dependency Direction Grep Commands

Run these to detect violations before committing:

```bash
# Schemas importing ORM models (violation: schema → model)
grep -rn "from app.db.models" app/schemas/

# Repos importing schemas (violation: repo → schema)
grep -rn "from app.schemas" app/repo/

# Routers importing repos directly (violation: router bypasses service)
grep -rn "from app.repo" app/routers/

# Routers importing ORM models (violation: router → model)
grep -rn "from app.db.models" app/routers/

# Models importing anything above them (violation: model → any outer layer)
grep -rn "from app.schemas\|from app.routers\|from app.services\|from app.repo" app/db/models/
```

---

## Transaction Scope Rules

| Scenario | Rule |
|----------|------|
| Single repo write | `flush()` in repo is fine — session commit managed by `get_db_session` |
| Multiple repo writes that must be atomic | `async with session.begin():` in the service method |
| Read-only service method | No transaction needed |
| Service calls service | Inner service must NOT start its own transaction — pass session or use same UoW |

The `get_db_session` dependency in `app/db/session.py` should commit on success and rollback on exception. If it only flushes, the outermost service method owning a multi-write operation must wrap it.

---

## How to Apply During Code Generation

1. **Before writing any import**: ask "which layer is this file in, and which layer am I importing from — does it flow inward?"
2. **When writing a service method** that calls >1 repo write: always add `async with session.begin():`.
3. **When writing a schema** with a `to_<Model>()` method: stop — move that method to the service.
4. **When writing a router** that imports anything from `app.repo` or `app.db`: stop — add a service method instead.
5. **Flag inline** as `# ARCH VIOLATION: <type> — move to <correct layer>` so the developer sees it immediately.
6. After detecting any violation, suggest the corrected pattern in full — don't just describe the fix.
