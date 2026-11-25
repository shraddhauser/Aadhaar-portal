#!/bin/bash
# AADHAAR PORTAL - COMMAND SHORTCUTS
# Run these commands to set up and launch the application

echo "======================================================================"
echo "AADHAAR PORTAL - QUICK COMMAND REFERENCE"
echo "======================================================================"
echo ""

# Display all commands
cat << 'EOF'

📌 SETUP COMMANDS (Run in order)

1️⃣  Generate Sample Data (12,500 records):
    python scripts/generate_sample_data.py

2️⃣  Update .env with your MySQL password:
    Edit .env → DB_PASSWORD=your_mysql_password

3️⃣  Create MySQL Database:
    mysql -u root -p"your_password" -e "CREATE DATABASE IF NOT EXISTS aadhaar_analytics;"

4️⃣  Initialize Database & Load Data:
    python scripts/setup_complete.py

5️⃣  Verify Data Was Loaded:
    python scripts/verify_database.py

6️⃣  Check Implementation is Complete:
    python CHECK_IMPLEMENTATION.py

---

🚀 RUN COMMANDS

Start Backend Server:
    cd backend
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Then open in browser:
    http://localhost:8000

Login:
    Username: admin
    Password: Admin@1234

---

🔧 UTILITY COMMANDS

View API Documentation (Swagger):
    http://localhost:8000/docs
    http://localhost:8000/redoc

Test Database Connection:
    python scripts/verify_database.py

Manually Load CSV Files:
    curl -X POST "http://localhost:8000/api/import/enrollments/upload" \
    -F "file=@data/api_data_aadhar_enrolment.csv" \
    -H "Authorization: Bearer TOKEN"

Check Ingestion Status:
    curl "http://localhost:8000/api/import/status" \
    -H "Authorization: Bearer TOKEN"

Get Forecast:
    curl "http://localhost:8000/api/import/predictive/forecast-enrollment?months_ahead=3" \
    -H "Authorization: Bearer TOKEN"

---

📚 DOCUMENTATION

Quick Start (5 minutes):
    cat QUICK_START.md

Complete Guide (Comprehensive):
    cat DATA_INTEGRATION_GUIDE.md

Implementation Details:
    cat IMPLEMENTATION_SUMMARY.md

Completion Status:
    cat EXECUTION_COMPLETE.md

---

🐛 TROUBLESHOOTING

Reset & Start Over:
    # Delete and recreate database
    mysql -u root -p"password" -e "DROP DATABASE aadhaar_analytics;"
    mysql -u root -p"password" -e "CREATE DATABASE aadhaar_analytics;"
    python scripts/setup_complete.py

Check Python Dependencies:
    pip list | grep -E "pandas|numpy|sqlalchemy|fastapi"

Reinstall Dependencies:
    pip install -r requirements.txt

View Detailed Logs:
    # Edit backend/routes/data_import.py and add logging

---

📊 DATA SUMMARY

Enrollment Records: 5,000+
Demographic Records: 3,000+
Biometric Records: 4,500+
Daily Statistics: 365 days
Regions: 10 (Indian states/districts)
Total Database Records: 12,500+

---

🎯 QUICK TEST

1. Generate data:
    python scripts/generate_sample_data.py

2. Setup database:
    python scripts/setup_complete.py

3. Verify:
    python scripts/verify_database.py

4. Start server:
    cd backend && python -m uvicorn main:app --reload

5. Open browser:
    http://localhost:8000

Expected Result: Dashboard shows real enrollment data from MySQL database.

---

✅ SUCCESS INDICATORS

- ✅ 5,000+ enrollment records in database
- ✅ 3,000+ demographic records
- ✅ 4,500+ biometric quality scores
- ✅ Live Statistics shows real data
- ✅ Past History shows real trends
- ✅ Insights shows real biometric scores
- ✅ Anomalies tab shows detected issues

---

💡 TIPS

- Sample data is generated in: data/api_data_aadhar_*.csv
- Database config is in: .env (keep this file secure!)
- Backend API docs: http://localhost:8000/docs
- Data pipelines: backend/data_ingestion.py
- Import endpoints: backend/routes/data_import.py

For more info, see QUICK_START.md or DATA_INTEGRATION_GUIDE.md

======================================================================"
EOF

echo ""
echo "For complete setup, follow QUICK_START.md or run CHECK_IMPLEMENTATION.py"
echo ""
