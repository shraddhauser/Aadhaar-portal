"""
Shared pytest fixtures.

Every test gets a fresh in-memory SQLite database (StaticPool, so all
sessions share one connection) wired into the app through FastAPI's
dependency override for get_db. No .env, network, or API keys are used.
"""

import os
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

# Configure the app *before* any backend module is imported.
os.environ["DB_ENGINE"] = "sqlite"
os.environ["DB_URL"] = "sqlite://"
os.environ["ENV"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-not-used-anywhere-else"
os.environ.pop("ANTHROPIC_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from backend.data_ingestion import DataIngestionPipeline  # noqa: E402
from backend.database import Base, get_db  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models.models import AdminUser, Enrollment, Region  # noqa: E402
from backend.routes.auth import pwd_context  # noqa: E402

ADMIN_USERNAME = "test-admin"
ADMIN_PASSWORD = "test-password-123"
VIEWER_USERNAME = "test-viewer"
VIEWER_PASSWORD = "viewer-password-123"

REGIONS = [
    ("MH-MUM", "Maharashtra", "Mumbai"),
    ("KA-BLR", "Karnataka", "Bengaluru"),
    ("DL-NDL", "Delhi", "New Delhi"),
]
GENDERS = ["Male", "Female"]
AGE_GROUPS = ["0-18", "19-35", "36-60", "60+"]
STATUSES = ["Pending", "Verified", "Rejected", "Generated"]
SEED_ROWS = 200
SEED_DAYS = 60


@dataclass(frozen=True)
class SeedRow:
    """One synthetic enrolment, kept so tests can compute expected values."""
    region_code: str
    day: date
    gender: str
    age_group: str
    status: str


def synthetic_enrollments(n: int = SEED_ROWS, days: int = SEED_DAYS) -> list[SeedRow]:
    """Deterministic rows across 3 regions, 2 genders, 4 age groups and `days` days."""
    today = date.today()
    return [
        SeedRow(
            region_code=REGIONS[i % len(REGIONS)][0],
            day=today - timedelta(days=i % days),
            gender=GENDERS[i % len(GENDERS)],
            age_group=AGE_GROUPS[i % len(AGE_GROUPS)],
            status=STATUSES[(i // 2) % len(STATUSES)],
        )
        for i in range(n)
    ]


def add_enrollments(db, rows: list[SeedRow]) -> None:
    """Insert rows and rebuild daily_stats with the app's own aggregation code."""
    region_ids = {r.region_code: r.region_id for r in db.query(Region).all()}
    db.add_all(
        Enrollment(
            region_id=region_ids[r.region_code],
            enrollment_date=r.day,
            gender=r.gender,
            age_group=r.age_group,
            enrollment_status=r.status,
            aadhaar_generated=r.status == "Generated",
        )
        for r in rows
    )
    db.commit()
    DataIngestionPipeline(db).aggregate_daily_stats()


@pytest.fixture
def db_session():
    """A fresh in-memory database with regions and two users, but no enrolments."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    db.add_all(Region(region_code=c, state_name=s, district_name=d) for c, s, d in REGIONS)
    db.add_all([
        AdminUser(username=ADMIN_USERNAME, password_hash=pwd_context.hash(ADMIN_PASSWORD),
                  full_name="Test Admin", role="SuperAdmin"),
        AdminUser(username=VIEWER_USERNAME, password_hash=pwd_context.hash(VIEWER_PASSWORD),
                  full_name="Test Viewer", role="Viewer"),
    ])
    db.commit()

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield db
    finally:
        app.dependency_overrides.pop(get_db, None)
        db.close()
        engine.dispose()


@pytest.fixture
def seed_rows(db_session) -> list[SeedRow]:
    """Seed ~200 synthetic enrolments and return them."""
    rows = synthetic_enrollments()
    add_enrollments(db_session, rows)
    return rows


@pytest.fixture
def client(db_session):
    """TestClient on an empty database (regions and users only)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def seeded_client(seed_rows, client):
    return client


def _login(client, username, password) -> dict:
    resp = client.post("/api/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def token(client) -> str:
    """A bearer token for the SuperAdmin test user."""
    resp = client.post("/api/auth/login",
                       data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(token) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers(client) -> dict:
    return _login(client, VIEWER_USERNAME, VIEWER_PASSWORD)
