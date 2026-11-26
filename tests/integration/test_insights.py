import pytest

from tests.conftest import add_enrollments, synthetic_enrollments

FORECAST_URL = "/api/import/predictive/forecast-enrollment"


@pytest.fixture
def four_months(db_session):
    """Enough history (>= 3 calendar months) for the forecast to run."""
    add_enrollments(db_session, synthetic_enrollments(n=360, days=120))


@pytest.mark.parametrize("months", [1, 3, 6, 12])
def test_forecast_returns_requested_horizon(client, auth_headers, four_months, months):
    resp = client.get(FORECAST_URL, params={"months_ahead": months}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    forecast = resp.json()["forecast"]
    assert len(forecast) == months
    assert all(v >= 0 for v in forecast)


@pytest.mark.parametrize("months", [0, 13])
def test_forecast_rejects_out_of_range_horizon(client, auth_headers, months):
    resp = client.get(FORECAST_URL, params={"months_ahead": months}, headers=auth_headers)
    assert resp.status_code == 422


def test_forecast_with_too_little_history_reports_error(client, auth_headers):
    resp = client.get(FORECAST_URL, headers=auth_headers)
    assert resp.status_code == 200
    assert "error" in resp.json()


def test_trends_forecast_values_are_non_negative(client, auth_headers, four_months):
    resp = client.get("/api/insights/trends-forecast", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["history"]
    assert all(h["enrollments"] >= 0 for h in body["history"])
    assert body["sma_3_month"] >= 0
    assert body["projected_next"] >= 0
    assert all(v >= 0 for v in body["ml_forecast"] or [])


def test_trends_forecast_on_empty_database(client, auth_headers):
    resp = client.get("/api/insights/trends-forecast", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["projected_next"] == 0
