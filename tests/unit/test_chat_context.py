"""The chatbot prompt must contain aggregates only, with a bounded size."""
import re

from backend.routes import chat
from tests.conftest import ADMIN_USERNAME, add_enrollments, synthetic_enrollments

ROW_LEVEL_MARKERS = [
    "enrollment_id", "update_id", "biometric_id", "admin_id", "password", "hash",
    ADMIN_USERNAME, "test-viewer",
]


def test_context_has_no_row_level_fields(db_session):
    add_enrollments(db_session, synthetic_enrollments(n=300, days=60))
    context = chat._gather_portal_context(db_session)
    for marker in ROW_LEVEL_MARKERS:
        assert marker not in context
    # Dates are only the report date, never per-record dates.
    assert len(re.findall(r"\d{4}-\d{2}-\d{2}", context)) == 0


def test_context_size_does_not_grow_with_row_count(db_session):
    add_enrollments(db_session, synthetic_enrollments(n=60, days=30))
    small = chat._gather_portal_context(db_session)
    add_enrollments(db_session, synthetic_enrollments(n=3000, days=30))
    large = chat._gather_portal_context(db_session)
    # Same lines, only bigger numbers (a few extra digits and separators).
    assert small.count("\n") == large.count("\n")
    assert abs(len(large) - len(small)) < 100


def test_context_is_capped(db_session, monkeypatch):
    monkeypatch.setattr(chat, "MAX_CONTEXT_CHARS", 50)
    context = chat._gather_portal_context(db_session)
    assert context.endswith("[dashboard data truncated]")
    assert len(context) <= 50 + len("\n[dashboard data truncated]")
