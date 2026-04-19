#!/usr/bin/env python3
import sqlite3
from pathlib import Path

paths = [
    Path('c:/Users/Nitin/Desktop/Personal Projects/Aadhaar Portal/aadhaar-portal/aadhaar_analytics.db'),
    Path('c:/Users/Nitin/Desktop/Personal Projects/Aadhaar Portal/aadhaar-portal/aadhaar-portal/aadhaar_analytics.db'),
]
for p in paths:
    print('\nChecking:', p)
    if not p.exists():
        print('  does not exist')
        continue
    conn = sqlite3.connect(p)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    print('  tables:', c.fetchall())
    try:
        c.execute('SELECT COUNT(*) FROM enrollments')
        print('  enrollments:', c.fetchone()[0])
    except Exception as e:
        print('  enrollments error:', e)
    conn.close()
