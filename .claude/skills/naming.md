---
name: naming
description: >
  Naming conventions checker for the Animal Shelter API. Enforces Clean Code naming,
  is_ booleans, smell detection, and project-specific suffixes. Run on any new code.
---

# /naming — Naming Conventions

## Core rules

| What | Rule | Example |
|------|------|---------|
| Booleans | `is_` / `has_` / `can_` prefix always | `is_active`, `has_passed_health_check` |
| Functions | verb + domain noun | `admit_animal()` not `process()` |
| Classes | noun phrase with role suffix | `AnimalAdmissionService` not `AnimalManager` |
| Enums | singular type, SCREAMING_SNAKE members | `class Gender(StrEnum): MALE = "male"` |
| Constants | SCREAMING_SNAKE, describe the rule | `MAX_ANIMALS_PER_ENCLOSURE = 5` |
| Files | singular snake_case | `animal.py`, `health_log.py` |

## Project-specific suffixes (enforce these)

- Models: `app/db/models/<entity>.py`
- Services: `app/services/<entity>_service.py`
- Schemas: `app/schemas/<entity>_request.py` / `<entity>_response.py`
- Routers: `app/routers/v1/<entity>_router.py`

## Abbreviations — always reject

`d`, `obj`, `val`, `tmp`, `cnt`, `dt`, `ts`, `repo`, `svc` → name the concept.
Exception: loop index `i` in a 2-line scope.

## Smells to flag

| Smell | Signal | Fix |
|-------|--------|-----|
| God class | one class does persistence + validation + business logic | Split by SRP |
| Primitive obsession | `gender: str`, `status: str` | Replace with `Gender` enum |
| Magic strings | `if status == "active"` | Extract to enum member |
| Long param list (>3) | `def create(name, gender, birth_date, notes, id)` | Use Pydantic schema |
| `manager`, `helper`, `utils` class names | vague responsibility | Name by what it actually does |

## Flag inline as

`# SMELL: <type> — consider <fix>`
