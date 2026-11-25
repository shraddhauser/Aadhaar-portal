#!/usr/bin/env python3
"""
scripts/demo_bootstrap.py
Prepare the database for the public demo (used as the Render start step).

If the database has no enrolments yet, it is built from data/*.csv with the
same steps as setup_complete.py. Then a read-only demo user (role Viewer) is
created from DEMO_USERNAME / DEMO_PASSWORD. Safe to run on every start: an
existing database is left as it is.

The demo data is synthetic (see docs/DATA.md).
"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import setup_complete  # noqa: E402
from create_admin import create_admin  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("demo_bootstrap")


def database_has_data() -> bool:
    from backend.database import SessionLocal
    from backend.models.models import Enrollment

    db = SessionLocal()
    try:
        return db.query(Enrollment).first() is not None
    finally:
        db.close()


def main() -> int:
    if not setup_complete.init_database_schema() or not setup_complete.seed_regions():
        return 1

    if database_has_data():
        logger.info("Database already has data; skipping CSV load.")
    elif not setup_complete.load_data():
        return 1

    username = os.getenv("DEMO_USERNAME", "demo").strip()
    password = os.getenv("DEMO_PASSWORD", "")
    if not password:
        logger.error("DEMO_PASSWORD is not set; no demo login was created.")
        return 1
    result = create_admin(username, password, reset=True, full_name="Demo Viewer", role="Viewer")
    logger.info("Demo user '%s' %s (role Viewer).", username, result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
