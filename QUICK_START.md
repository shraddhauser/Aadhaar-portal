# Aadhaar Portal - Quick Start Guide

## What We've Implemented

✅ **Real Data Integration Pipeline**
- Data ingestion scripts for enrollment, demographic, and biometric data
- Automatic data cleaning and normalization
- Missing value handling and data validation
- CSV to MySQL database import with error tracking

✅ **Backend API Endpoints**
- `/api/import/enrollments/upload` - Upload enrollment CSV
- `/api/import/demographic/upload` - Upload demographic/update CSV
- `/api/import/biometric/upload` - Upload biometric CSV
- `/api/import/status` - Check ingestion status
- `/api/import/predictive/forecast-enrollment` - Forecast trends
- `/api/import/predictive/growth-patterns` - Identify patterns

✅ **Predictive Models**
- Exponential smoothing for enrollment forecasting
- Growth pattern recognition by region
- Anomaly detection (low biometric quality, high rejection rates)
- Real-time analytics from database queries

✅ **Sample Data**
- 5,000+ enrollment records (gender, age, status, region)
- 3,000+ demographic/update records (type, status)
- 4,500+ biometric quality scores (fingerprint, iris, photo)
- Realistic distributions and date ranges

✅ **Frontend Updates**
- Live Statistics displays real enrollment data
- Past History shows actual trend analysis
- Insights page shows real biometric scores
- Anomalies panel flags detected issues

---

## Quick Start (5 minutes)

### 1. Generate Sample Data
```bash
python scripts/generate_sample_data.py
```

Creates:
- `data/api_data_aadhar_enrolment.csv`
- `data/api_data_aadhar_demographic.csv`
- `data/api_data_aadhar_biometric.csv`

### 2. Setup MySQL Database

**First time setup:**

```bash
# Option A: If MySQL has no password
mysql -u root -e "CREATE DATABASE IF NOT EXISTS aadhaar_analytics;"

# Option B: If MySQL password is set (replace 'password' with your password)
mysql -u root -p"password" -e "CREATE DATABASE IF NOT EXISTS aadhaar_analytics;"
```

**Then update .env:**
```
DB_USER=root
DB_PASSWORD=password     # Your MySQL password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aadhaar_analytics
```

### 3. Load Data into Database

```bash
python scripts/setup_complete.py
```

This will:
- ✓ Test MySQL connection
- ✓ Create database schema
- ✓ Seed 10 regions (Indian states/districts)
- ✓ Load 12,500+ records
- ✓ Aggregate daily statistics
- ✓ Detect anomalies

### 4. Start Backend

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open Dashboard

```
http://localhost:8000
```

Login: `admin` / `Admin@1234`

---

## Your Real Data

If you have your own CSV files, use the API endpoints:

**Python:**
```python
import requests

# Login
login_response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={"username": "admin", "password": "Admin@1234"}
)
token = login_response.json()['access_token']

headers = {"Authorization": f"Bearer {token}"}

# Upload enrollment data
with open('your_enrollments.csv', 'rb') as f:
    requests.post(
        'http://localhost:8000/api/import/enrollments/upload',
        files={'file': f},
        headers=headers
    )
```

**cURL:**
```bash
# Get token
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@1234"}' \
  | jq -r '.access_token')

# Upload file
curl -X POST "http://localhost:8000/api/import/enrollments/upload" \
  -F "file=@your_enrollments.csv" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Data Flow

```
CSV Files                    Python Script              MySQL Database
           ↓                         ↓                         ↓
[Enrollment.csv] ──────→ [DataIngestion] ────────→ [enrollments]
[Demographic.csv] ──────→ [Clean & Normalize] ─→ [updates]
[Biometric.csv] ────────→ [Validate & Map] ────→ [biometric_data]
                              ↓
                        [Aggregate Stats]
                              ↓
                        [Detect Anomalies]
                              ↓
         Backend API ← Query Real Data
           ↓
       Frontend Dashboard
```

---

## Available Data

After loading sample data:

**Enrollments (5,000 records)**
- enrollment_date: distributed across 365 days
- gender: 45% Male, 35% Female, 20% Other
- age_group: 0-18, 19-35, 36-60, 60+
- status: 20% Pending, 50% Verified, 20% Rejected, 10% Generated
- region: 10 Indian states/districts

**Updates (3,000 records)**
- update_type: Name, Address, Mobile, Email, Biometric, Photo, DOB
- status: 20% Pending, 60% Approved, 20% Rejected
- distributed across same date range and regions

**Biometric Quality (4,500 records)**
- fingerprint_quality: mostly 70-98, ~10% low quality (30-60)
- iris_quality: mostly 70-98, ~12% low quality (25-60)
- photo_quality: mostly 75-99, ~8% low quality (40-65)

**Regions (10 seeded)**
```
MH-MUM: Maharashtra, Mumbai
MH-PUN: Maharashtra, Pune
MH-NSK: Maharashtra, Nashik
KA-BLR: Karnataka, Bengaluru
KA-MYS: Karnataka, Mysuru
TN-CHN: Tamil Nadu, Chennai
TN-CBE: Tamil Nadu, Coimbatore
UP-LKO: Uttar Pradesh, Lucknow
UP-AGR: Uttar Pradesh, Agra
DL-NDL: Delhi, New Delhi
```

---

## Dashboard Features

### Live Statistics Tab
- KPIs: Total enrollments, updates, generated, pending
- Gender distribution (pie chart)
- Age-group distribution (bar chart)
- Enrollment status breakdown
- Update type frequency

### Past History Tab
- Monthly enrollment trends (bar + line chart)
- Regional comparison (top regions by enrollment)
- Year-over-year growth (line chart)
- Update history breakdown by type/status

### Insights Tab
- Biometric quality scores (real aggregated data)
- AI-powered recommendations
- Predictive forecast (next 3 months)
- Anomaly detection results

### Anomalies Tab
- Detected irregularities (duplicates, low quality, surges)
- Severity classification (Low, Medium, High, Critical)
- Resolution tracking

---

## API Reference

### Live Data Endpoints
```
GET  /api/live/summary                    → KPI cards (enrollments, updates, etc.)
GET  /api/live/gender-split               → Gender distribution (30 days)
GET  /api/live/age-split                  → Age-group distribution (30 days)
GET  /api/live/status-breakdown           → Enrollment status breakdown
GET  /api/live/update-types               → Update type frequency (30 days)
GET  /api/live/regions                    → Available regions for filters
```

### Historical Endpoints
```
GET  /api/history/monthly-trend?year=2024 → Monthly enrollments/updates
GET  /api/history/regional-comparison     → Regional comparison (date range)
GET  /api/history/yearly-growth           → Year-over-year growth
GET  /api/history/update-history          → Update history breakdown
```

### Insights Endpoints
```
GET  /api/insights/recommendations        → AI recommendations
GET  /api/insights/biometric-quality      → Biometric scores (avg)
GET  /api/insights/trends-forecast        → Predictive forecast
```

### Data Import Endpoints
```
POST /api/import/enrollments/upload       → Upload enrollment CSV
POST /api/import/demographic/upload       → Upload demographic CSV
POST /api/import/biometric/upload         → Upload biometric CSV
GET  /api/import/status                   → Data ingestion status
GET  /api/import/predictive/forecast-enrollment → ML forecast
GET  /api/import/predictive/growth-patterns    → Growth patterns
```

---

## Troubleshooting

### "Database connection failed"
Check .env file has correct MySQL credentials and MySQL is running:
```bash
mysql -u root -p"password" -e "SELECT 1;"
```

### "No data in dashboard"
Run data loading:
```bash
python scripts/setup_complete.py
```

### "Module not found" errors
Install dependencies:
```bash
pip install -r requirements.txt
```

### "CSV parsing errors"
Ensure CSV columns match expected format (see DATA_INTEGRATION_GUIDE.md)

---

## Project Structure

```
aadhaar-portal/
├── backend/
│   ├── data_ingestion.py          ← Data cleaning & normalization
│   ├── routes/
│   │   ├── data_import.py         ← Data import API endpoints
│   │   ├── live_stats.py          ← Real-time statistics
│   │   ├── history.py             ← Historical analysis
│   │   └── insights.py            ← Predictive analytics
│   ├── models/models.py           ← Database schema (SQLAlchemy)
│   └── main.py                    ← FastAPI app entry point
├── data/                          ← Sample CSV files
│   ├── api_data_aadhar_enrolment.csv
│   ├── api_data_aadhar_demographic.csv
│   └── api_data_aadhar_biometric.csv
├── scripts/
│   ├── generate_sample_data.py    ← Generate sample data
│   ├── load_data_to_db.py         ← Load into database
│   └── setup_complete.py          ← Complete setup
├── .env                           ← Database configuration
└── DATA_INTEGRATION_GUIDE.md      ← Detailed documentation
```

---

## Next Steps

1. ✅ Real data loaded into MySQL
2. ✅ Backend APIs query actual data
3. ✅ Frontend displays real analytics
4. ✅ Predictive models trained on historical data
5. Next: Set up scheduled data refresh (cron job)
6. Next: Integrate with UIDAI API for live enrollment data

---

For detailed information, see [DATA_INTEGRATION_GUIDE.md](DATA_INTEGRATION_GUIDE.md)
