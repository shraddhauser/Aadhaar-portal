# MySQL Setup Guide for Aadhaar Portal

## Issue Found
The MySQL root user authentication failed. This typically happens on fresh Windows installations where the root password wasn't set.

## ✅ Quick Fix - Use Administrator Command Prompt

### Step 1: Open Administrator Command Prompt
- Press `Win + R`
- Type: `cmd`
- Right-click and select "Run as Administrator"

### Step 2: Navigate to MySQL Bin Directory
```cmd
cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"
```

### Step 3: Reset Root Password
```cmd
mysql -u root
```

If you get "Access denied", that means root has no password. Try:
```cmd
mysqld --skip-grant-tables
```

Then in another Admin command prompt:
```cmd
cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"
mysql -u root

mysql> FLUSH PRIVILEGES;
mysql> ALTER USER 'root'@'localhost' IDENTIFIED BY 'password';
mysql> EXIT;
```

### Step 4: Create Database
In Admin Command Prompt:
```cmd
cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"
mysql -u root -ppassword

mysql> CREATE DATABASE IF NOT EXISTS aadhaar_analytics;
mysql> SHOW DATABASES;
mysql> EXIT;
```

If connection fails with "Access denied", the password is still not working. Try:

### Step 4 Alternative: Empty Password
Update `.env` file:
```
DB_PASSWORD=
```

Then test:
```cmd
mysql -u root

mysql> CREATE DATABASE IF NOT EXISTS aadhaar_analytics;
mysql> SHOW DATABASES;
mysql> EXIT;
```

## Step 5: Verify .env Configuration
The `.env` file should match your MySQL setup:

```
DB_USER=root
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aadhaar_analytics
```

## Step 6: Run Setup Script
Once MySQL is configured, run:
```bash
cd "c:\Users\Nitin\Desktop\Personal Projects\Adhaar Portal\aadhaar-portal\aadhaar-portal"
python scripts/setup_complete.py
```

## Step 7: Verify Database
```bash
python scripts/verify_database.py
```

Should show:
- 5000 enrollments loaded
- 3000 demographic updates loaded
- 4500 biometric records loaded
- 365 daily statistics

## Step 8: Start Backend Server
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open: http://localhost:8000

## Troubleshooting

### "Access denied for user 'root'@'localhost'"
- MySQL is running but password wrong
- Solution: Run Step 3 above to reset password

### "Can't connect to MySQL server on 'localhost'"
- MySQL service not running
- Check: `Get-Service mysql* | Select-Object Status,Name`
- Start it: `Get-Service mysql* | Start-Service`

### "ERROR 1007: Can't create database; database exists"
- Database already exists (good!)
- Just run: `python scripts/setup_complete.py`
- It will skip creation and load data

### "ERROR 1045: Access denied (using password: NO)"
- Root account exists but needs password
- Run Step 3 with password reset option

## What's Ready to Go
✅ FastAPI backend fully coded  
✅ 12,500+ sample records generated  
✅ Data ingestion pipeline complete  
✅ 6 new API endpoints created  
✅ Predictive analytics models ready  
✅ All Python dependencies installed  

## Next After MySQL Setup
1. Run: `python scripts/setup_complete.py` → Creates tables, seeds regions, loads data
2. Run: `python scripts/verify_database.py` → Confirms data loaded successfully
3. Start backend: `cd backend && python -m uvicorn main:app --reload`
4. Open: http://localhost:8000
5. Login with: **admin** / **Admin@1234**
