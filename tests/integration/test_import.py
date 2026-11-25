from datetime import date

import pytest

import backend.routes.data_import as data_import
from backend.models.models import Enrollment

URL = "/api/import/enrollments/upload"
VALID_CSV = (
    "enrollment_date,gender,age,enrollment_status,region_code\n"
    "2026-01-01,Male,30,Verified,MH-MUM\n"
    "2026-01-02,F,10,Generated,KA-BLR\n"
    "2026-01-03,Female,70,Pending,DL-NDL\n"
).encode()


def _upload(client, headers, content, filename="data.csv", url=URL):
    return client.post(url, headers=headers, files={"file": (filename, content, "text/csv")})


def test_valid_csv_adds_rows(client, auth_headers, db_session):
    before = db_session.query(Enrollment).count()
    resp = _upload(client, auth_headers, VALID_CSV)
    assert resp.status_code == 200, resp.text
    assert resp.json()["records_ingested"] == 3
    assert db_session.query(Enrollment).count() == before + 3


@pytest.mark.xfail(strict=True, reason="Known bug: uploaded enrolment dates are replaced with "
                                       "the upload date (see test_ingestion_cleaning.py)")
def test_upload_keeps_the_dates_from_the_csv(client, auth_headers, db_session):
    _upload(client, auth_headers, VALID_CSV)
    dates = sorted(e.enrollment_date for e in db_session.query(Enrollment).all())
    assert dates == [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]


def test_missing_column_is_400_and_names_it(client, auth_headers, db_session):
    resp = _upload(client, auth_headers, b"enrollment_date,age,region_code\n2026-01-01,30,MH-MUM\n")
    assert resp.status_code == 400
    assert resp.json()["detail"]["missing_columns"] == ["gender"]
    assert db_session.query(Enrollment).count() == 0


def test_biometric_missing_scores_are_listed(client, auth_headers):
    resp = _upload(client, auth_headers, b"enrollment_date,iris_quality\n2026-01-01,80\n",
                   url="/api/import/biometric/upload")
    assert resp.status_code == 400
    missing = resp.json()["detail"]["missing_columns"]
    assert missing == ["fingerprint_quality or fp_quality", "photo_quality or photo_qual"]


def test_empty_file_is_400(client, auth_headers):
    assert _upload(client, auth_headers, b"").status_code == 400


def test_header_only_is_400(client, auth_headers):
    resp = _upload(client, auth_headers, b"enrollment_date,gender,age,region_code\n")
    assert resp.status_code == 400


@pytest.mark.parametrize("filename,content", [
    ("photo.png", b"\x89PNG\r\n\x1a\n"),
    ("data.xlsx", b"PK\x03\x04"),
    ("data.csv", bytes(range(256)) * 10),  # binary content with a .csv name
])
def test_non_csv_is_400(client, auth_headers, filename, content):
    assert _upload(client, auth_headers, content, filename=filename).status_code == 400


def test_oversized_file_is_413(client, auth_headers, monkeypatch):
    monkeypatch.setattr(data_import, "MAX_UPLOAD_BYTES", 50)
    assert _upload(client, auth_headers, VALID_CSV).status_code == 413


def test_no_token_is_401(client):
    assert _upload(client, {}, VALID_CSV).status_code == 401


def test_non_admin_role_is_403(client, viewer_headers):
    assert _upload(client, viewer_headers, VALID_CSV).status_code == 403
    assert client.get("/api/import/status", headers=viewer_headers).status_code == 403
