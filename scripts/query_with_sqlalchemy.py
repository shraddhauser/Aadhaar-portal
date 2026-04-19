from pathlib import Path
import sys
proj = Path(__file__).resolve().parent.parent / 'aadhaar-portal'
sys.path.insert(0, str(proj))
from backend.database import SessionLocal
from backend.models.models import Enrollment, DailyStat

db = SessionLocal()
try:
    enroll_count = db.query(Enrollment).count()
    daily_count = db.query(DailyStat).count()
    print('SQLAlchemy enroll_count=', enroll_count)
    print('SQLAlchemy daily_stats_count=', daily_count)
finally:
    db.close()
