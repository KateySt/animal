import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import AnimalFactory, AnimalTranslationFactory, HealthLogFactory, HealthLogTranslationFactory


def _animal_payload(owner_id: uuid.UUID, name: str = "Buddy") -> dict:
    return {
        "owner_id": str(owner_id),
        "gender": "male",
        "birth_date": "2020-06-15",
        "translations": [{"locale": "en", "name": name, "caretaker_notes": None}],
        "health_logs": [{"translations": [{"locale": "en", "procedure_name": "Initial exam", "examination_findings": None}]}],
    }


@pytest.mark.integration
async def test_get_animals_without_token_returns_401(client: AsyncClient):
    resp = await client.get("/v1/animals")
    assert resp.status_code == 401


@pytest.mark.integration
async def test_get_animals_empty_returns_empty_list(auth_client: AsyncClient):
    resp = await auth_client.get("/v1/animals")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"] == []
    assert data["total_count"] == 0


@pytest.mark.integration
async def test_get_animals_returns_paginated_results(auth_client: AsyncClient, db_session: AsyncSession, user):
    for i in range(3):
        animal = AnimalFactory(owner_id=user.id)
        AnimalTranslationFactory(parent_id=animal.id, locale="en", name=f"Animal {i}")
        log = HealthLogFactory(animal_id=animal.id)
        HealthLogTranslationFactory(parent_id=log.id, locale="en", procedure_name="Checkup")
    await db_session.flush()

    resp = await auth_client.get("/v1/animals?page=1&items_per_page=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 2
    assert data["total_count"] == 3


@pytest.mark.integration
async def test_get_animal_by_id_returns_animal_data(auth_client: AsyncClient, db_session: AsyncSession, user):
    animal = AnimalFactory(owner_id=user.id, gender="female")
    AnimalTranslationFactory(parent_id=animal.id, locale="en", name="Luna")
    log = HealthLogFactory(animal_id=animal.id)
    HealthLogTranslationFactory(parent_id=log.id, locale="en", procedure_name="Vaccination")
    await db_session.flush()

    resp = await auth_client.get(f"/v1/animals/{animal.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["gender"] == "female"
    assert any(t["name"] == "Luna" for t in data["translations"])
    assert len(data["health_logs"]) == 1


@pytest.mark.integration
async def test_get_animal_by_id_nonexistent_returns_404(auth_client: AsyncClient):
    resp = await auth_client.get(f"/v1/animals/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.integration
async def test_create_animal_returns_201_with_data(auth_client: AsyncClient, user):
    resp = await auth_client.post("/v1/animals", json=_animal_payload(user.id, name="Rex"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["gender"] == "male"
    assert any(t["name"] == "Rex" for t in data["translations"])
    assert len(data["health_logs"]) == 1
    assert "id" in data


@pytest.mark.integration
async def test_create_animal_without_en_translation_returns_422(auth_client: AsyncClient, user):
    payload = {
        **_animal_payload(user.id),
        "translations": [{"locale": "uk", "name": "Рекс", "caretaker_notes": None}],
    }
    resp = await auth_client.post("/v1/animals", json=payload)
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_animal_without_health_log_returns_422(auth_client: AsyncClient, user):
    payload = {**_animal_payload(user.id), "health_logs": []}
    resp = await auth_client.post("/v1/animals", json=payload)
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_animal_nonexistent_owner_returns_404(auth_client: AsyncClient):
    resp = await auth_client.post("/v1/animals", json=_animal_payload(uuid.uuid4()))
    assert resp.status_code == 404


@pytest.mark.integration
async def test_create_animal_without_token_returns_401(client: AsyncClient, user):
    resp = await client.post("/v1/animals", json=_animal_payload(user.id))
    assert resp.status_code == 401


@pytest.mark.integration
async def test_create_animal_without_create_scope_returns_403(read_only_client: AsyncClient):
    resp = await read_only_client.post("/v1/animals", json=_animal_payload(uuid.uuid4()))
    assert resp.status_code == 403


@pytest.mark.integration
async def test_update_animal_gender_returns_updated_value(auth_client: AsyncClient, db_session: AsyncSession, user):
    animal = AnimalFactory(owner_id=user.id, gender="female")
    AnimalTranslationFactory(parent_id=animal.id, locale="en", name="Mia")
    log = HealthLogFactory(animal_id=animal.id)
    HealthLogTranslationFactory(parent_id=log.id, locale="en", procedure_name="Check")
    await db_session.flush()

    resp = await auth_client.patch(f"/v1/animals/{animal.id}", json={"gender": "male"})
    assert resp.status_code == 200
    assert resp.json()["gender"] == "male"


@pytest.mark.integration
async def test_update_animal_translation_returns_updated_name(auth_client: AsyncClient, db_session: AsyncSession, user):
    animal = AnimalFactory(owner_id=user.id)
    AnimalTranslationFactory(parent_id=animal.id, locale="en", name="OldName")
    log = HealthLogFactory(animal_id=animal.id)
    HealthLogTranslationFactory(parent_id=log.id, locale="en", procedure_name="Check")
    await db_session.flush()

    resp = await auth_client.patch(
        f"/v1/animals/{animal.id}",
        json={"translations": [{"locale": "en", "name": "NewName", "caretaker_notes": None}]},
    )
    assert resp.status_code == 200
    assert any(t["name"] == "NewName" for t in resp.json()["translations"])


@pytest.mark.integration
async def test_update_animal_nonexistent_returns_404(auth_client: AsyncClient):
    resp = await auth_client.patch(f"/v1/animals/{uuid.uuid4()}", json={"gender": "female"})
    assert resp.status_code == 404


@pytest.mark.integration
async def test_delete_animal_returns_204_and_removes_record(auth_client: AsyncClient, db_session: AsyncSession, user):
    animal = AnimalFactory(owner_id=user.id)
    AnimalTranslationFactory(parent_id=animal.id, locale="en", name="ToDelete")
    log = HealthLogFactory(animal_id=animal.id)
    HealthLogTranslationFactory(parent_id=log.id, locale="en", procedure_name="Check")
    await db_session.flush()

    resp = await auth_client.delete(f"/v1/animals/{animal.id}")
    assert resp.status_code == 204

    resp = await auth_client.get(f"/v1/animals/{animal.id}")
    assert resp.status_code == 404


@pytest.mark.integration
async def test_delete_animal_nonexistent_returns_404(auth_client: AsyncClient):
    resp = await auth_client.delete(f"/v1/animals/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.integration
async def test_delete_animal_without_token_returns_401(client: AsyncClient, db_session: AsyncSession, user):
    animal = AnimalFactory(owner_id=user.id)
    AnimalTranslationFactory(parent_id=animal.id, locale="en", name="Protected")
    await db_session.flush()

    resp = await client.delete(f"/v1/animals/{animal.id}")
    assert resp.status_code == 401
