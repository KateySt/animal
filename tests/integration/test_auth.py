import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_register_returns_201_with_user_data(client: AsyncClient):
    resp = await client.post("/v1/auth/register", json={"email": "newuser@test.com", "password": "SecurePass123!"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@test.com"
    assert "hashed_password" not in data
    assert "id" in data


@pytest.mark.integration
async def test_register_duplicate_email_returns_409(client: AsyncClient):
    payload = {"email": "dup@test.com", "password": "SecurePass123!"}
    r1 = await client.post("/v1/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/v1/auth/register", json=payload)
    assert r2.status_code == 409


@pytest.mark.integration
@pytest.mark.parametrize("password", ["short", "", "1234567"])
async def test_register_invalid_password_returns_422(client: AsyncClient, password: str):
    resp = await client.post("/v1/auth/register", json={"email": "val@test.com", "password": password})
    assert resp.status_code == 422


@pytest.mark.integration
async def test_register_invalid_email_returns_422(client: AsyncClient):
    resp = await client.post("/v1/auth/register", json={"email": "not-an-email", "password": "SecurePass123!"})
    assert resp.status_code == 422


@pytest.mark.integration
async def test_login_returns_access_token(client: AsyncClient):
    await client.post("/v1/auth/register", json={"email": "login@test.com", "password": "SecurePass123!"})
    resp = await client.post("/v1/auth/login", data={"username": "login@test.com", "password": "SecurePass123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.integration
async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post("/v1/auth/register", json={"email": "wrongpass@test.com", "password": "SecurePass123!"})
    resp = await client.post("/v1/auth/login", data={"username": "wrongpass@test.com", "password": "WrongPass!"})
    assert resp.status_code == 401


@pytest.mark.integration
async def test_login_nonexistent_user_returns_404(client: AsyncClient):
    resp = await client.post("/v1/auth/login", data={"username": "ghost@test.com", "password": "AnyPass123!"})
    assert resp.status_code == 404


@pytest.mark.integration
async def test_logout_returns_204(client: AsyncClient):
    await client.post("/v1/auth/register", json={"email": "logout@test.com", "password": "SecurePass123!"})
    login = await client.post("/v1/auth/login", data={"username": "logout@test.com", "password": "SecurePass123!"})
    assert login.status_code == 200
    refresh_token = login.cookies.get("refresh")
    resp = await client.post("/v1/auth/logout", cookies={"refresh": refresh_token})
    assert resp.status_code == 204


@pytest.mark.integration
async def test_protected_endpoint_without_token_returns_401(client: AsyncClient):
    resp = await client.get("/v1/animals")
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers or resp.json().get("detail")
