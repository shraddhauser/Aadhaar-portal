from datetime import date
from pathlib import Path
import sys
proj = Path(__file__).resolve().parent.parent / 'aadhaar-portal'
sys.path.insert(0, str(proj))
from backend.database import SessionLocal
from backend.models.models import Enrollment, Region

db = SessionLocal()
try:
    region = db.query(Region).first()
    print('region found:', region.region_code if region else None)
    if not region:
        print('No region to attach to; aborting')
    else:
        e = Enrollment(region_id=region.region_id, enrollment_date=date.today(), gender='Male', age_group='19-35', enrollment_status='Verified', aadhaar_generated=False)
        db.add(e)
        db.commit()
        print('Inserted enrollment id', e.enrollment_id)
        cnt = db.query(Enrollment).count()
        print('SQLAlchemy count now', cnt)
finally:
    db.close()

# check via sqlite3
import sqlite3
p = r'c:\Users\Nitin\Desktop\Personal Projects\Adhaar Portal\aadhaar-portal\aadhaar-portal\aadhaar_analytics.db'
conn = sqlite3.connect(p)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM enrollments')
print('sqlite count', cur.fetchone()[0])
conn.close()
