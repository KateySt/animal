# Naming Review Skill

## Trigger
Use this skill whenever you write or review Python code. Run it before finalizing any function, class, variable, or parameter name.

## Core Philosophy (Clean Code + Clean Architecture)

Names must answer **WHY** this thing exists, not **WHAT** it technically does.

> Bad: `process_data(d)` — describes a mechanical action on an opaque input  
> Good: `archive_expired_health_records(overdue_logs)` — reveals intent and domain meaning

---

## Checklist — run mentally on every identifier

### 1. No abbreviations, no single-letter names
Reject unless it's a universally understood domain term (e.g., `id`, `url`).

| Banned | Replace with |
|--------|--------------|
| `d`, `obj`, `val`, `tmp` | name the concept it holds |
| `cnt`, `num`, `qty` | `count`, `number`, `quantity` |
| `dt`, `ts` | `recorded_at`, `expires_on` |
| `repo`, `svc` | `animal_repository`, `health_log_service` |
| `get_all` alone | `fetch_animals_for_shelter`, `list_active_health_logs` |

**Exception**: loop variables in a 2-line scope (`for i, item in enumerate(...)`) are fine.

### 2. No dual meanings — one name, one concept
If you have to write "or" to explain what a name means, rename it.

| Smell | Fix |
|-------|-----|
| `status` (is it HTTP? animal health? order state?) | `animal_health_status`, `http_response_code` |
| `data` (dict? list? raw bytes?) | `animal_payload`, `serialized_health_log` |
| `handle` (process? return a handle? catch?) | `register_incoming_animal`, `catch_db_error` |
| `manager` (anti-pattern class name) | `AnimalAdmissionCoordinator`, `HealthLogScheduler` |
| `helper`, `utils`, `misc` (module names) | name by what the helpers actually do |

### 3. Booleans — always `is_` / `has_` / `can_` prefix
Every boolean-holding name must read as a yes/no question.

```python
# Wrong
active = True
deleted = False
health_check = True

# Correct
is_active = True
is_deleted = False
has_passed_health_check = True
```

In SQLAlchemy models use the same rule:
```python
is_neutered: Mapped[bool] = mapped_column(Boolean, default=False)
is_vaccinated: Mapped[bool] = mapped_column(Boolean, default=False)
```

### 4. Functions — verb + domain noun, not generic verbs
| Generic (what) | Specific (why) |
|----------------|----------------|
| `process()` | `admit_animal_to_shelter()` |
| `check()` | `verify_vaccination_is_current()` |
| `update()` | `reschedule_health_examination()` |
| `get()` | `fetch_animal_by_microchip_id()` |
| `run()` | `execute_daily_health_report_generation()` |

### 5. Classes — noun phrases that reflect domain responsibility
| Smell | Better |
|-------|--------|
| `AnimalManager` | `AnimalAdmissionService` |
| `DataProcessor` | `HealthLogExporter` |
| `BaseHandler` | `HttpRequestDispatcher` |
| `Utils` | split into focused classes |

### 6. Enums — singular noun for type, SCREAMING_SNAKE for members
```python
class AnimalGender(StrEnum):   # not "Genders", not "GenderType"
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"
```

### 7. Constants — SCREAMING_SNAKE, explain business rule
```python
MAX_ANIMALS_PER_ENCLOSURE = 5          # capacity rule, not just a "limit"
HEALTH_RECHECK_INTERVAL_DAYS = 30     # domain policy
DEFAULT_QUARANTINE_DURATION_DAYS = 14
```

---

## Code Smell Detector

While reviewing names, simultaneously check for these smells and call them out:

| Smell | Signal | Pattern to suggest |
|-------|--------|--------------------|
| **God class** | one class does persistence + validation + business logic + formatting | Split by SRP; use Repository, Service, Schema layers (already present in this project) |
| **Primitive obsession** | `gender: str`, `status: str`, `id: str` instead of domain types | Replace with `Gender` enum, `AnimalStatus` enum, `UUID` |
| **Feature envy** | method uses another class's data more than its own | Move method to the class whose data it uses |
| **Anemic domain model** | model has only fields, zero behaviour | Ask: should any invariant live here as a method? |
| **Magic strings/numbers** | `if status == "active"` or `if count > 20` | Extract to enum member or named constant |
| **Long parameter list** (>3 params) | `def create(name, gender, birth_date, notes, enclosure_id)` | Introduce a dataclass/Pydantic schema as a parameter object |
| **Redundant comment** | comment restates what the name already says | Delete the comment; improve the name instead |

---

## Design Pattern Radar

Spot opportunities to suggest (never force) these patterns:

| Situation in code | Pattern to consider |
|-------------------|---------------------|
| Multiple filter/sort strategies dispatched by string key (already in `base_repository.py`) | **Strategy** — `_STRATEGIES` dict is correct; flag if new strategies are added inline instead of to the dict |
| Building complex query objects step-by-step | **Builder** |
| Need to decouple event (animal admitted) from reaction (send notification, log audit) | **Observer / Event Bus** |
| Different animal types need different behaviour | **Template Method** or **Visitor** |
| Wrapping external services (email, S3) so they're swappable | **Adapter** |
| Single shared DB session / config instance | **Singleton** (already handled by FastAPI DI — note it if duplicated) |
| Repeated `if isinstance(x, AnimalA)... elif isinstance(x, AnimalB)` | **Polymorphism / Strategy** |

---

## Project-Specific Conventions (this codebase)

- Models live in `app/db/models/` — name files after the entity, singular: `animal.py`, `health_log.py`
- Repositories in `app/repo/` — suffix `_repository`: `animal_repository.py`
- Services in `app/services/` — suffix `_service`: `animal_admission_service.py`
- Schemas in `app/schemas/` — suffix by role: `animal_request.py`, `animal_response.py`
- Enums in `app/db/enums.py` — add new domain enums here, never inline strings in models
- Filter keys use `field__op` double-underscore convention — respect it, document new ops in `FilterOptions`

---

## How to Apply During Code Generation

1. **Before writing** any name, ask: "Does this name explain WHY this exists in the domain?"
2. **After writing** a function, read its signature aloud — if it sounds like an IT operation rather than a business action, rename it.
3. **Booleans**: scan every `bool`-typed field/variable — add `is_` / `has_` / `can_` if missing.
4. **No single-word class names** for services or repositories — always `<Domain><Role>`.
5. **Flag smells inline** as `# SMELL: <type> — consider <pattern>` so the developer sees it.
6. **Never shorten** a name to save typing. IDEs autocomplete; readers pay the cost of ambiguity for months.
