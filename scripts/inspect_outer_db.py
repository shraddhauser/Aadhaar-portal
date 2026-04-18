import sqlite3
p = r'c:\Users\Nitin\Desktop\Personal Projects\Adhaar Portal\aadhaar-portal\aadhaar_analytics.db'
print('DB path:', p)
conn = sqlite3.connect(p)
c = conn.cursor()
try:
    c.execute('SELECT name FROM sqlite_master WHERE type="table"')
    print('tables:', c.fetchall())
except Exception as e:
    print('Error listing tables', e)

try:
    c.execute('SELECT COUNT(*) FROM enrollments')
    print('enroll_count', c.fetchone()[0])
    c.execute('SELECT MIN(enrollment_date), MAX(enrollment_date) FROM enrollments')
    print('enroll minmax', c.fetchone())
    c.execute('SELECT COUNT(*) FROM daily_stats')
    print('daily_stats count', c.fetchone()[0])
    c.execute('SELECT DISTINCT stat_date FROM daily_stats ORDER BY stat_date')
    print('stat_date sample', c.fetchall()[:20])
except Exception as e:
    print('error', e)
conn.close()
