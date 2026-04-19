# Aadhaar Portal - Real Data Integration Guide

This guide explains how to set up real Aadhaar data integration with your local MySQL database.

## Prerequisites

- **Python 3.9+** with pip
- **MySQL Server** running locally (Host: localhost, Port: 3306)
- **FastAPI** backend installed (see requirements.txt)
- **pandas** and **numpy** for data processing

## Step 1: Database Configuration

### 1.1 Create .env file

Copy the template and configure your MySQL credentials:

```bash
cp .env.template .env
```

Edit `.env` with your MySQL credentials:

```ini
DB_USER=root              # Your MySQL username
DB_PASSWORD=your_password # Your MySQL password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aadhaar_analytics
SECRET_KEY=your-secret-key-here
```

### 1.2 Create MySQL Database

```sql
-- Login to MySQL
mysql -u root -p

-- Create database (if not exists)
CREATE DATABASE IF NOT EXISTS aadhaar_analytics;
```

## Step 2: Generate Sample Data

The project includes scripts to generate realistic sample datasets matching your schema:

```bash
# From project root
cd scripts
python generate_sample_data.py
```

This generates three CSV files in `data/` directory:
- `api_data_aadhar_enrolment.csv` (5000 records)
- `api_data_aadhar_demographic.csv` (3000 records)
- `api_data_aadhar_biometric.csv` (4500 records)

## Step 3: Initialize Database & Load Data

### 3.1 Initialize schema and seed regions

```bash
cd scripts
python load_data_to_db.py
```

This script will:
1. Create all database tables
2. Seed default regions (10 Indian states/districts)
3. Load enrollment, demographic, and biometric data
4. Aggregate daily statistics
5. Detect anomalies

**Expected output:**
```
========================================================================
AADHAAR PORTAL - DATABASE INITIALIZATION & DATA LOADING
========================================================================

✓ Database schema created
✓ Regions seeded
Processing api_data_aadhar_enrolment.csv...
✓ Loaded 5000 enrollment records
Processing api_data_aadhar_demographic.csv...
✓ Loaded 3000 demographic records
Processing api_data_aadhar_biometric.csv...
✓ Loaded 4500 biometric records
✓ Aggregated stats for 365 days
✓ Detected 15 anomalies

========================================================================
DATA LOADING SUMMARY
========================================================================
Enrollments loaded:  5000
Demographics loaded: 3000
Biometrics loaded:   4500

Total records: 12,500
========================================================================
```

## Step 4: Start Backend Server

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API is now running at `http://localhost:8000`

**Check health:**
```bash
curl http://localhost:8000/health
# Response: {"status": "ok", "message": "Aadhaar Analytics Portal API is running."}
```

## Step 5: Access Dashboard

Open browser and navigate to:
```
http://localhost:8000
```

Login credentials:
- **Username:** admin
- **Password:** Admin@1234

## Data Integration API Endpoints

### Upload Enrollment Data
```bash
curl -X POST "http://localhost:8000/api/import/enrollments/upload" \
  -F "file=@data/api_data_aadhar_enrolment.csv" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Upload Demographic Data
```bash
curl -X POST "http://localhost:8000/api/import/demographic/upload" \
  -F "file=@data/api_data_aadhar_demographic.csv" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Upload Biometric Data
```bash
curl -X POST "http://localhost:8000/api/import/biometric/upload" \
  -F "file=@data/api_data_aadhar_biometric.csv" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Ingestion Status
```bash
curl "http://localhost:8000/api/import/status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
# {
#   "enrollments": 5000,
#   "updates": 3000,
#   "biometric_records": 4500,
#   "daily_stats": 365,
#   "total_records": 12500
# }
```

### Get Predictive Forecast
```bash
curl "http://localhost:8000/api/import/predictive/forecast-enrollment?months_ahead=3" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
# {
#   "historical": [...],
#   "forecast": [1245, 1380, 1510],
#   "confidence": 0.75
# }
```

### Get Growth Patterns
```bash
curl "http://localhost:8000/api/import/predictive/growth-patterns" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Data Cleaning & Normalization

The ingestion pipeline automatically handles:

### Enrollment Data
- ✓ Date parsing and validation
- ✓ Gender normalization (M/F/O → Male/Female/Other)
- ✓ Age to age-group mapping (Age → 0-18, 19-35, 36-60, 60+)
- ✓ Status validation (Pending, Verified, Rejected, Generated)
- ✓ Region code mapping from district names
- ✓ Missing value handling with defaults

### Demographic Data
- ✓ Date parsing and validation
- ✓ Update type normalization (Various formats → Standardized)
- ✓ Status validation (Pending, Approved, Rejected)
- ✓ Region code mapping
- ✓ Missing value handling

### Biometric Data
- ✓ Quality score normalization (0-100 range)
- ✓ Invalid value clipping
- ✓ Missing quality scores filled with realistic values
- ✓ Linking to enrollment records by date

## Using Your Own Datasets

### Format Requirements

**enrollment_data.csv:**
```
enrollment_date,gender,age,enrollment_status,region_code
2024-01-15,Male,28,Generated,MH-MUM
2024-01-16,Female,45,Verified,KA-BLR
```

**demographic_data.csv:**
```
update_date,update_type,update_status,region_code
2024-01-15,Name,Approved,MH-MUM
2024-01-16,Address,Pending,KA-BLR
```

**biometric_data.csv:**
```
enrollment_date,fingerprint_quality,iris_quality,photo_quality
2024-01-15,85,92,88
2024-01-16,78,85,91
```

### Region Codes Available
```
MH-MUM, MH-PUN, MH-NSK     # Maharashtra
KA-BLR, KA-MYS             # Karnataka
TN-CHN, TN-CBE             # Tamil Nadu
UP-LKO, UP-AGR             # Uttar Pradesh
DL-NDL                     # Delhi
```

## Frontend Integration

The frontend automatically displays:

### Live Statistics Tab
- Real-time enrollment counts
- Gender and age-group distribution
- Enrollment status breakdown
- Update type distribution

### Past History Tab
- Monthly trend analysis
- Regional comparison heatmap
- Year-over-year growth
- Update history breakdown

### Insights Tab
- Biometric quality scores (real aggregated data)
- AI-powered recommendations
- Predictive forecasts
- Anomaly detection results

### Anomalies Tab
- Detected irregularities
- Severity classification
- Resolution tracking

## Database Schema

### Key Tables

**enrollments** (5000+ records)
- enrollment_id, region_id, enrollment_date
- gender, age_group, enrollment_status
- aadhaar_generated

**updates** (3000+ records)
- update_id, region_id, update_date
- update_type, update_status

**biometric_data** (4500+ records)
- biometric_id, enrollment_id
- fingerprint_quality, iris_quality, photo_quality

**daily_stats** (365+ records)
- stat_id, stat_date, region_id
- total_enrollments, total_updates, aadhaar_generated
- pending_count, rejected_count

**anomalies** (auto-generated)
- anomaly_id, region_id, anomaly_type
- severity, description, detected_on

## Predictive Models

### Enrollment Forecast
- **Algorithm:** Exponential Smoothing
- **Input:** Historical monthly enrollment counts
- **Output:** 3-month forward forecast with confidence score
- **Location:** `/api/import/predictive/forecast-enrollment`

### Growth Pattern Recognition
- **Algorithm:** Regional aggregation analysis
- **Input:** Daily stats by region
- **Output:** Growth trends by region
- **Location:** `/api/import/predictive/growth-patterns`

### Anomaly Detection
- **Triggers:** Low biometric quality, high rejection rates
- **Output:** Flagged records with severity levels
- **Automatic:** Runs on data import

## Troubleshooting

### "Database connection failed"
```bash
# Check MySQL is running
mysql -u root -p -e "SELECT 1"

# Verify .env credentials
cat .env
```

### "No data showing in dashboard"
```bash
# Check data was loaded
python scripts/load_data_to_db.py

# Verify record counts
curl "http://localhost:8000/api/import/status"
```

### "Import API returns 401 Unauthorized"
```bash
# Get token from login
# Use: Authorization: Bearer <YOUR_TOKEN>
```

### "CSV parsing errors"
- Ensure CSV column names match expected format
- Check UTF-8 encoding
- Verify date formats (YYYY-MM-DD)
- See data_ingestion.py for detailed error messages in logs

## Performance Tips

- **Large datasets:** Import in batches (5000 records per file)
- **Aggregation:** Runs after each import to maintain daily_stats
- **Anomaly detection:** CPU-bound; takes 1-2 seconds per 1M+ records
- **Database:** Enable indexes on frequently queried columns

## Data Privacy & Anonymization

- Biometric data is stored as quality scores only (no raw biometric data)
- No PII (names, documents, raw images) stored
- Region-level aggregation for trend analysis
- All audit logs tracked automatically

## Next Steps

1. ✓ Dashboard displays real enrollment/demographic data
2. ✓ Predictive models analyze historical trends
3. ✓ Anomaly detection flags quality issues
4. ✓ Insights recommendations based on real patterns
5. Next: Export reports, set up scheduled data refresh, integrate with UIDAI API

---

**For more details, see:**
- Backend API docs: `http://localhost:8000/docs` (Swagger UI)
- Models: `backend/models/models.py`
- Data ingestion: `backend/data_ingestion.py`
- Import routes: `backend/routes/data_import.py`
