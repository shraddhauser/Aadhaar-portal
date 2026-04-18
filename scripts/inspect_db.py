import sqlite3
from pathlib import Path
p = Path(__file__).parent.parent / 'aadhaar_analytics.db'
print('DB path:', p)
conn = sqlite3.connect(p)
c = conn.cursor()
try:
    c.execute('SELECT DISTINCT stat_date FROM daily_stats ORDER BY stat_date')
    rows = c.fetchall()
    print('daily_stat dates count=', len(rows))
    for r in rows[:100]:
        print(r)
    c.execute('SELECT COUNT(*) FROM daily_stats')
    print('total daily_stats rows', c.fetchone()[0])
except Exception as e:
    print('Error querying daily_stats:', e)

try:
    c.execute('SELECT MIN(enrollment_date), MAX(enrollment_date), COUNT(*) FROM enrollments')
    print('enroll min,max,count', c.fetchone())
except Exception as e:
    print('Error querying enrollments:', e)

conn.close()
