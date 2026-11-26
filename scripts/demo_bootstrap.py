#!/usr/bin/env python3
"""
scripts/demo_bootstrap.py
Prepare the database for the public demo (used as the Render start step).

If the database has no enrolments yet, it is built with the same steps as
setup_complete.py. By default the synthetic CSVs are regenerated first, with a
fixed seed and dates ending today, so "last 30 days" views have data; set
DEMO_FRESH_DATA=false to load the committed data/*.csv instead. Then a read-only demo user (role Viewer) is
created from DEMO_USERNAME / DEMO_PASSWORD. Safe to run on every start: an
existing database is left as it is.

The demo data is synthetic (see docs/DATA.md).
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_sample_data  # noqa: E402
import setup_complete  # noqa: E402
from create_admin import create_admin  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("demo_bootstrap")

DEMO_SEED = 2026
DEMO_DAYS = 730


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
    elif os.getenv("DEMO_FRESH_DATA", "true").strip().lower() in ("0", "false", "no"):
        if not setup_complete.load_data():
            return 1
    else:
        with tempfile.TemporaryDirectory() as tmp:
            generate_sample_data.main(days=DEMO_DAYS, seed=DEMO_SEED, out_dir=Path(tmp))
            if not setup_complete.load_data(tmp):
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
