from datetime import timedelta

from jose import jwt

from backend.routes.auth import ALGORITHM, create_access_token
from tests.conftest import ADMIN_PASSWORD, ADMIN_USERNAME

PROTECTED = "/api/auth/me"


def _login(client, username, password):
    return client.post("/api/auth/login", data={"username": username, "password": password})


def test_correct_credentials_return_token(client):
    resp = _login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["role"] == "SuperAdmin"


def test_token_grants_access(client, auth_headers):
    resp = client.get(PROTECTED, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == ADMIN_USERNAME


def test_wrong_password_is_401(client):
    assert _login(client, ADMIN_USERNAME, "not-the-password").status_code == 401


def test_unknown_user_is_401(client):
    assert _login(client, "nobody", ADMIN_PASSWORD).status_code == 401


def test_protected_route_without_token_is_401(client):
    assert client.get(PROTECTED).status_code == 401


def test_expired_token_is_401(client):
    expired = create_access_token({"sub": ADMIN_USERNAME}, expires_delta=timedelta(minutes=-5))
    resp = client.get(PROTECTED, headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


def test_token_signed_with_other_key_is_401(client):
    forged = jwt.encode({"sub": ADMIN_USERNAME}, "some-other-key", algorithm=ALGORITHM)
    resp = client.get(PROTECTED, headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401


def test_tampered_token_is_401(client, token):
    header, payload, signature = token.split(".")
    tampered = ".".join([header, payload, signature[:-2] + ("AA" if signature[-2:] != "AA" else "BB")])
    resp = client.get(PROTECTED, headers={"Authorization": f"Bearer {tampered}"})
    assert resp.status_code == 401


def test_token_for_deleted_user_is_401(client):
    ghost = create_access_token({"sub": "deleted-user"}, expires_delta=timedelta(minutes=5))
    resp = client.get(PROTECTED, headers={"Authorization": f"Bearer {ghost}"})
    assert resp.status_code == 401
