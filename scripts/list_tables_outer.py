#!/usr/bin/env python3
import sqlite3
from pathlib import Path
p = Path(__file__).parent / 'aadhaar_analytics.db'
print('DB path:', p)
conn = sqlite3.connect(p)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print('tables:', c.fetchall())
conn.close()
