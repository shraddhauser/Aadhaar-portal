from datetime import date, timedelta

from tests.conftest import REGIONS, SeedRow, add_enrollments

PER_DAY = 2
SPIKE_REGION = REGIONS[1][0]


def _flat_rows(spike_factor: int = 1) -> list[SeedRow]:
    """PER_DAY enrolments per region for the last 8 days; today x spike_factor in one region."""
    today = date.today()
    rows = []
    for offset in range(8):
        day = today - timedelta(days=offset)
        for code, _, _ in REGIONS:
            n = PER_DAY * (spike_factor if offset == 0 and code == SPIKE_REGION else 1)
            rows += [SeedRow(code, day, "Male", "19-35", "Verified")] * n
    return rows


def test_spike_today_is_flagged_for_that_region_only(client, auth_headers, db_session):
    add_enrollments(db_session, _flat_rows(spike_factor=5))
    resp = client.get("/api/anomalies/detect-surges", headers=auth_headers)
    assert resp.status_code == 200
    surges = resp.json()["surges"]
    assert [s["region_code"] for s in surges] == [SPIKE_REGION]
    assert surges[0]["today"] == PER_DAY * 5
    assert surges[0]["avg_7d"] == PER_DAY
    assert surges[0]["pct_change"] == 400.0


def test_flat_data_has_no_surges(client, auth_headers, db_session):
    add_enrollments(db_session, _flat_rows(spike_factor=1))
    resp = client.get("/api/anomalies/detect-surges", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["surges"] == []


def test_threshold_is_respected(client, auth_headers, db_session):
    add_enrollments(db_session, _flat_rows(spike_factor=5))  # +400 %
    resp = client.get("/api/anomalies/detect-surges", params={"threshold_pct": 450},
                      headers=auth_headers)
    assert resp.json()["surges"] == []


def test_list_on_empty_database(client, auth_headers):
    resp = client.get("/api/anomalies/list", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []
