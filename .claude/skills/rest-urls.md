---
name: rest-urls
description: >
  REST URL design checklist for the Animal Shelter API. Use whenever adding a new
  router, endpoint, or prefix — ensures URL structure follows REST best practices
  and is consistent with the existing `app/routers/` and `app/main.py` conventions.
---

## REST URL Rules — Animal Shelter API

### 1. Resource nouns, never verbs

URLs name resources; HTTP methods express the action.

| Wrong (verb in URL) | Correct |
|---------------------|---------|
| `/animals/create` | `POST /animals` |
| `/animals/getAll` | `GET /animals` |
| `/animals/deleteAnimal/1` | `DELETE /animals/{animal_id}` |
| `/animals/updateStatus` | `PATCH /animals/{animal_id}/status` |
| `/animals/searchByName` | `GET /animals?name=Rex` |

### 2. Plural nouns for collections, singular segment for a specific resource

```
GET  /animals               → collection
GET  /animals/{animal_id}   → one animal
GET  /animals/{animal_id}/health-logs         → sub-collection
GET  /animals/{animal_id}/health-logs/{log_id} → one log
```

Never mix singular/plural for the same resource across routes.

### 3. kebab-case for multi-word path segments

```
/health-logs      ✓
/healthLogs       ✗  (camelCase — not REST standard)
/health_logs      ✗  (snake_case — use only in query params)
```

Query parameter names use **snake_case**:
```
GET /animals?is_vaccinated=true&sort_by=name
```

### 4. HTTP method → status code mapping (enforce in every router)

| Method | Success code | FastAPI constant |
|--------|--------------|-----------------|
| POST (create) | 201 | `status.HTTP_201_CREATED` |
| GET | 200 | default, no need to set |
| PUT / PATCH | 200 | default |
| DELETE | 204 | `status.HTTP_204_NO_CONTENT` |

Never return 200 for a create; never return a body on 204.

### 5. Router prefix and tag convention (app/main.py)

```python
app.include_router(animal_router,     prefix="/animals",      tags=["Animals"])
app.include_router(health_log_router, prefix="/health-logs",  tags=["Health Logs"])
```

- Prefix = plural kebab-case resource name.
- Tag = Title Case, shown in Swagger UI.
- Nested resource routers get their own prefix when the sub-resource is independently addressable (e.g., `/health-logs/{log_id}`); otherwise they live under the parent prefix.

### 6. Path parameter naming

Always `{resource_id}` — never `{id}` alone (ambiguous in nested routes).

```python
@router.get("/{animal_id}", response_model=AnimalResponse)
@router.get("/{animal_id}/health-logs/{log_id}", response_model=HealthLogResponse)
```

### 7. Filtering, sorting, pagination — always query params, never path

```
GET /animals?species=dog&is_vaccinated=true&sort_by=name&order=asc&page=1&page_size=20
```

This project's `BaseRepository` already supports `filter_by`, `sort_by`, `order`, `page`, `page_size` — wire them directly as `Query(...)` params.

### 8. Actions that don't map cleanly to CRUD

Use a sub-resource noun that names the state change:

```
POST /animals/{animal_id}/adoption      # initiate adoption
DELETE /animals/{animal_id}/adoption    # cancel adoption
POST /animals/{animal_id}/quarantine    # place in quarantine
PATCH /animals/{animal_id}/status       # update health/shelter status
```

Never `POST /animals/{animal_id}/setStatus` or `/animals/adopt`.

### 9. Versioning (when needed)

Prefix via `root_path` or router prefix — never in the resource path.

```python
# main.py — preferred for this project
app = FastAPI(root_path="/api/v1")

# Or at router level
app.include_router(animal_router, prefix="/v1/animals")
```

Current setup uses `root_path="/api"` — add version segment there first.

### 10. Router file checklist — run before committing any new router

- [ ] `APIRouter()` with no prefix (prefix set in `main.py`)
- [ ] Every route has `response_model=` explicitly set
- [ ] POST → `status_code=status.HTTP_201_CREATED`
- [ ] DELETE → `status_code=status.HTTP_204_NO_CONTENT`, `response_model=None`
- [ ] Path params named `{resource_id}`, kebab-case segments
- [ ] No DB logic — router calls service only
- [ ] Router registered in `main.py` with plural kebab-case prefix and Title Case tag

### Example — correct router skeleton for a new resource

```python
# app/routers/health_log_router.py
from fastapi import APIRouter, Depends, status
from app.schemas.health_log import HealthLogCreate, HealthLogResponse
from app.services import get_health_log_service
from app.services.health_log_service import HealthLogService

router = APIRouter()


@router.get("", response_model=list[HealthLogResponse])
async def list_health_logs(
    animal_id: UUID | None = Query(None),
    service: HealthLogService = Depends(get_health_log_service),
) -> list[HealthLogResponse]:
    return await service.list_health_logs(animal_id=animal_id)


@router.get("/{log_id}", response_model=HealthLogResponse)
async def fetch_health_log(
    log_id: UUID,
    service: HealthLogService = Depends(get_health_log_service),
) -> HealthLogResponse:
    return await service.fetch_health_log_by_id(log_id)


@router.post("", response_model=HealthLogResponse, status_code=status.HTTP_201_CREATED)
async def record_health_log(
    payload: HealthLogCreate,
    service: HealthLogService = Depends(get_health_log_service),
) -> HealthLogResponse:
    return await service.record_health_log(payload)


@router.delete("/{log_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def remove_health_log(
    log_id: UUID,
    service: HealthLogService = Depends(get_health_log_service),
) -> None:
    await service.remove_health_log(log_id)
```

```python
# app/main.py — register it
app.include_router(health_log_router, prefix="/health-logs", tags=["Health Logs"])
```
