# 🚀 QUICK TEST GUIDE - Backend Running NOW

## Current Status
✅ Backend server: **Running at http://localhost:8000**  
✅ All Python dependencies: **Installed**  
✅ FastAPI app: **Loaded**  
⏳ MySQL Database: **Awaiting configuration**

---

## 🧪 Test What's Working Right Now

### 1. Test API Documentation (No database needed!)
```
Open in browser: http://localhost:8000/docs
```
You'll see:
- ✅ All 20+ API endpoints listed
- ✅ Swagger interactive documentation
- ✅ Try-it-out buttons for endpoints

### 2. Test Authentication Endpoint
```
# In PowerShell/Command Prompt:
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"Admin@1234"}'
```

Expected response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {"id": 1, "username": "admin"}
}
```

### 3. View Frontend
```
Open: http://localhost:8000
```
Should show: Login page with Aadhaar Portal branding

### 4. Check API Status
```
curl http://localhost:8000/api/monitoring/health
```

Expected:
```json
{
  "status": "healthy",
  "database": "not_connected",
  "timestamp": "2025-04-17T20:46:30Z"
}
```

---

## ⚙️ Next: Configure Database (15 mins)

### Easy Way - Reset MySQL Password

**In Administrator Command Prompt:**

```cmd
REM Step 1: Navigate to MySQL bin
cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"

REM Step 2: Connect as root (should work now or ask for password)
mysql -u root

REM If connected, run:
```

```sql
-- Set the password
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'password';
CREATE DATABASE IF NOT EXISTS aadhaar_analytics;
EXIT;
```

---

## 🔄 One-Line Setup (When MySQL Ready)

After MySQL is configured with root/password, run ONCE:

```bash
cd "c:\Users\Nitin\Desktop\Personal Projects\Adhaar Portal\aadhaar-portal\aadhaar-portal"
python scripts/setup_complete.py
```

This will:
1. ✅ Test MySQL connection
2. ✅ Create database schema
3. ✅ Seed 10 regions
4. ✅ Load 5000 enrollments
5. ✅ Load 3000 demographic updates
6. ✅ Load 4500 biometric records
7. ✅ Aggregate daily statistics
8. ✅ Detect anomalies

---

## 📊 After Setup - Test Real Data

### Get Ingestion Status
```bash
curl http://localhost:8000/api/import/status
```

Response will show:
```json
{
  "enrollments_loaded": 5000,
  "demographic_updates_loaded": 3000,
  "biometric_records_loaded": 4500,
  "daily_stats": 365,
  "total_records": 12500,
  "anomalies_detected": 45
}
```

### Get Enrollment Forecast
```bash
curl "http://localhost:8000/api/import/predictive/forecast-enrollment?months_ahead=3"
```

Returns 3-month forecast with growth trends.

### Get Growth Patterns
```bash
curl http://localhost:8000/api/import/predictive/growth-patterns
```

Returns regional analysis with highest growth.

---

## 🎯 Dashboard Login (After Setup)

Once database is loaded:

1. Go to: http://localhost:8000
2. Login with:
   - **Username**: admin
   - **Password**: Admin@1234
3. Dashboard displays:
   - Live stats (real-time DB queries)
   - 5000 enrollment records
   - Regional breakdown
   - Anomaly alerts
   - Historical trends

---

## 🐛 Troubleshooting

### "Cannot connect to localhost:8000"
- Check terminal output: `INFO: Uvicorn running on http://0.0.0.0:8000`
- If not there, backend didn't start
- Solution: Run again:
  ```bash
  cd "c:\Users\Nitin\Desktop\Personal Projects\Adhaar Portal\aadhaar-portal\aadhaar-portal"
  python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
  ```

### "Access denied for user 'root'@'localhost'"
- MySQL is running but password wrong
- See: MYSQL_SETUP.md for reset instructions
- Quick fix: Reset in Admin Command Prompt:
  ```cmd
  cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"
  mysql -u root
  FLUSH PRIVILEGES;
  ALTER USER 'root'@'localhost' IDENTIFIED BY 'password';
  ```

### "ModuleNotFoundError" or "No module named"
- Run from correct directory:
  ```bash
  cd "c:\Users\Nitin\Desktop\Personal Projects\Adhaar Portal\aadhaar-portal\aadhaar-portal"
  ```
- Reinstall dependencies:
  ```bash
  pip install -q -r requirements.txt
  ```

### Dashboard shows "No data"
- Database not yet loaded
- Run: `python scripts/setup_complete.py`
- Verify with: `python scripts/verify_database.py`

---

## 📈 What You Can See Right Now

✅ **API Documentation**: http://localhost:8000/docs  
✅ **Swagger UI**: Full interactive API explorer  
✅ **Login Page**: http://localhost:8000 (login.html being served)  
✅ **Auth Endpoint**: POST /api/auth/login (test above)  
✅ **Health Check**: GET /api/monitoring/health  

## 📈 What You Can See After DB Setup

✅ **Real Dashboard**: Live statistics from 12,500 records  
✅ **Enrollment Forecast**: 3-month ML prediction  
✅ **Growth Patterns**: Regional analysis  
✅ **Anomalies**: Biometric quality alerts  
✅ **Historical Data**: Time-series trends  
✅ **Data Export**: Download CSV reports  

---

## ⏱️ Time Breakdown

| Task | Time |
|------|------|
| MySQL Configuration | 5-10 min |
| Run Setup Script | 2-3 min |
| Verify Data | 1 min |
| Full Dashboard Ready | ~15 min total |

---

## 🎊 You're Done!

Backend is live and ready. Just need to:
1. Configure MySQL
2. Run setup script
3. Dashboard automatically shows real data

👉 **Next Step**: See MYSQL_SETUP.md for database configuration
