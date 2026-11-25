"""
The server-side export is a JSON summary report; CSV and PDF files are
built in the browser (frontend/js/app.js: exportCSV / exportPDF).
"""
from datetime import date, timedelta

URL = "/api/export/summary-report"


def test_summary_report_schema(seeded_client, auth_headers):
    resp = seeded_client.get(URL, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    body = resp.json()
    assert set(body) == {"report_date", "period", "kpis", "top_regions", "unresolved_anomalies"}
    assert set(body["kpis"]) == {"enrollments", "updates", "generated", "pending", "rejected"}
    for region in body["top_regions"]:
        assert set(region) == {"state", "district", "enrollments"}


def test_summary_report_totals_cover_last_30_days(seeded_client, auth_headers, seed_rows):
    since = date.today() - timedelta(days=30)
    recent = [r for r in seed_rows if r.day >= since]
    body = seeded_client.get(URL, headers=auth_headers).json()
    assert body["kpis"]["enrollments"] == len(recent)
    assert body["kpis"]["generated"] == sum(r.status == "Generated" for r in recent)
    regions = body["top_regions"]
    assert len(regions) <= 5
    assert [r["enrollments"] for r in regions] == sorted((r["enrollments"] for r in regions), reverse=True)
    assert sum(r["enrollments"] for r in regions) == len(recent)


def test_summary_report_requires_token(client):
    assert client.get(URL).status_code == 401
