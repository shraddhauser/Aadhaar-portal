from datetime import date

import pytest
from fastapi.testclient import TestClient

import backend.routes.live_stats as live_stats
from backend.main import CORS_ORIGINS, app
from backend.models.models import Anomaly, Region


# ---------- CORS ----------

def test_cors_allows_configured_origin(client):
    origin = CORS_ORIGINS[0]
    resp = client.get("/health", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") == origin


def test_cors_rejects_unknown_origin(client):
    resp = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in resp.headers


# ---------- error handling ----------

def test_unhandled_error_returns_json_500_without_details(db_session, auth_headers, monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(live_stats, "date", type("D", (), {"today": staticmethod(boom)}))
    with TestClient(app, raise_server_exceptions=False) as c:
        resp = c.get("/api/live/summary", headers=auth_headers)
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal server error"}
    assert "secret internal detail" not in resp.text
    assert "secret internal detail" in caplog.text  # logged server-side


# ---------- pagination ----------

@pytest.fixture
def many_anomalies(db_session):
    region = db_session.query(Region).first()
    db_session.add_all(
        Anomaly(region_id=region.region_id, anomaly_type="Surge", severity="Low",
                description=f"a{i}", detected_on=date(2026, 1, 1 + i % 28))
        for i in range(30)
    )
    db_session.commit()


def test_anomaly_list_limit_and_offset(client, auth_headers, many_anomalies):
    first = client.get("/api/anomalies/list", params={"limit": 10}, headers=auth_headers).json()
    second = client.get("/api/anomalies/list", params={"limit": 10, "offset": 10},
                        headers=auth_headers).json()
    everything = client.get("/api/anomalies/list", headers=auth_headers).json()
    assert len(first) == 10 and len(second) == 10 and len(everything) == 30
    assert {a["anomaly_id"] for a in first}.isdisjoint(a["anomaly_id"] for a in second)
    assert first + second == everything[:20]


@pytest.mark.parametrize("url", [
    "/api/anomalies/list",
    "/api/history/regional-comparison",
    "/api/history/update-history",
])
@pytest.mark.parametrize("params", [{"limit": 501}, {"limit": 0}, {"offset": -1}])
def test_pagination_bounds_are_enforced(client, auth_headers, url, params):
    assert client.get(url, params=params, headers=auth_headers).status_code == 422


def test_regional_comparison_pages(seeded_client, auth_headers):
    params = {"start_date": "2000-01-01", "end_date": "2100-01-01"}
    full = seeded_client.get("/api/history/regional-comparison", params=params,
                             headers=auth_headers).json()
    page = seeded_client.get("/api/history/regional-comparison",
                             params={**params, "limit": 1, "offset": 1}, headers=auth_headers).json()
    assert len(full) == 3
    assert page == full[1:2]
