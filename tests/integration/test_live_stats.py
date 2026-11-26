from collections import Counter
from datetime import date, timedelta

from tests.conftest import REGIONS


def test_summary_matches_seeded_latest_day(seeded_client, auth_headers, seed_rows):
    latest = max(r.day for r in seed_rows)
    rows = [r for r in seed_rows if r.day == latest]

    resp = seeded_client.get("/api/live/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["date"] == str(latest)
    assert body["enrollments"] == len(rows)
    assert body["generated"] == sum(r.status == "Generated" for r in rows)
    assert body["pending"] == sum(r.status == "Pending" for r in rows)
    assert body["rejected"] == sum(r.status == "Rejected" for r in rows)
    assert body["updates"] == 0


def test_summary_filters_by_region(seeded_client, auth_headers, seed_rows):
    latest = max(r.day for r in seed_rows)
    code = REGIONS[0][0]
    expected = sum(r.day == latest and r.region_code == code for r in seed_rows)
    resp = seeded_client.get("/api/live/summary", params={"region_code": code}, headers=auth_headers)
    assert resp.json()["enrollments"] == expected


def test_gender_split_all_time_adds_up_to_total(seeded_client, auth_headers, seed_rows):
    resp = seeded_client.get("/api/live/gender-split", params={"days": 0}, headers=auth_headers)
    assert resp.status_code == 200
    counts = {g["gender"]: g["count"] for g in resp.json()}
    assert sum(counts.values()) == len(seed_rows)
    assert counts == dict(Counter(r.gender for r in seed_rows))


def test_gender_split_default_window_is_last_30_days(seeded_client, auth_headers, seed_rows):
    since = date.today() - timedelta(days=30)
    expected = sum(r.day >= since for r in seed_rows)
    resp = seeded_client.get("/api/live/gender-split", headers=auth_headers)
    assert sum(g["count"] for g in resp.json()) == expected


def test_regions_lists_exactly_the_seeded_regions(seeded_client, auth_headers):
    resp = seeded_client.get("/api/live/regions", headers=auth_headers)
    assert resp.status_code == 200
    assert sorted(r["region_code"] for r in resp.json()) == sorted(c for c, _, _ in REGIONS)


def test_empty_database_returns_zeros(client, auth_headers):
    resp = client.get("/api/live/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    for key in ("enrollments", "updates", "generated", "pending", "rejected"):
        assert body[key] == 0
    assert client.get("/api/live/gender-split", headers=auth_headers).json() == []
