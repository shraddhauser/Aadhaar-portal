#!/usr/bin/env python3
import sqlite3
from pathlib import Path

db = Path(__file__).parent.parent / 'aadhaar_analytics.db'
if not db.exists():
    print('DB not found:', db)
    raise SystemExit(1)
conn = sqlite3.connect(db)
c = conn.cursor()
for q,label in [
    ("SELECT MIN(enrollment_date), MAX(enrollment_date), COUNT(*) FROM enrollments", 'enrollments'),
    ("SELECT MIN(stat_date), MAX(stat_date), COUNT(*) FROM daily_stats", 'daily_stats'),
    ("SELECT MIN(update_date), MAX(update_date), COUNT(*) FROM updates", 'updates'),
]:
    try:
        c.execute(q)
        print(label, 'min,max,count ->', c.fetchone())
    except Exception as e:
        print(label, 'query error:', e)
conn.close()
