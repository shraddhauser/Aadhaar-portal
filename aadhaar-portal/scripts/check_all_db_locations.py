#!/usr/bin/env python3
from pathlib import Path
import sqlite3

paths = [
    Path('c:/Users/Nitin/Desktop/Personal Projects/Adhaar Portal/aadhaar-portal/scripts/aadhaar_analytics.db'),
    Path('c:/Users/Nitin/Desktop/Personal Projects/Adhaar Portal/aadhaar-portal/aadhaar_analytics.db'),
    Path('c:/Users/Nitin/Desktop/Personal Projects/Adhaar Portal/aadhaar-portal/aadhaar-portal/aadhaar_analytics.db'),
]
for p in paths:
    print('\nChecking', p)
    if not p.exists():
        print('  not found')
        continue
    conn = sqlite3.connect(p)
    c = conn.cursor()
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        print('  tables:', c.fetchall())
        c.execute('SELECT COUNT(*) FROM daily_stats')
        print('  daily_stats count:', c.fetchone()[0])
        c.execute('SELECT COUNT(*) FROM enrollments')
        print('  enrollments count:', c.fetchone()[0])
    except Exception as e:
        print('  error querying:', e)
    conn.close()
