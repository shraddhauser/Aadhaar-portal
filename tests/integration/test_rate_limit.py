from tests.conftest import ADMIN_PASSWORD, ADMIN_USERNAME


def test_sixth_login_in_a_minute_is_429(client):
    statuses = [
        client.post("/api/auth/login",
                    data={"username": ADMIN_USERNAME, "password": "wrong-password"}).status_code
        for _ in range(6)
    ]
    assert statuses == [401] * 5 + [429]


def test_limit_also_blocks_correct_password(client):
    for _ in range(5):
        client.post("/api/auth/login", data={"username": "x", "password": "y"})
    resp = client.post("/api/auth/login",
                       data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert resp.status_code == 429


def test_chat_is_rate_limited(client, auth_headers, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)  # 503s still count
    statuses = [client.post("/api/chat/ask", headers=auth_headers,
                            json={"message": "hi"}).status_code for _ in range(11)]
    assert statuses == [503] * 10 + [429]
