"""
IMPLEMENTATION CHECKLIST - Verify all components are in place
Run this to confirm successful implementation
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
REQUIRED_FILES = {
    "Backend Modules": {
        "backend/data_ingestion.py": "Data cleaning & ingestion pipeline",
        "backend/routes/data_import.py": "Data import API endpoints",
    },
    "Scripts": {
        "scripts/generate_sample_data.py": "Sample data generator",
        "scripts/load_data_to_db.py": "Database initialization",
        "scripts/setup_complete.py": "Complete setup workflow",
        "scripts/verify_database.py": "Database verification",
    },
    "Configuration": {
        ".env": "Environment variables",
        ".env.template": "Environment template",
        "requirements.txt": "Python dependencies",
    },
    "Documentation": {
        "QUICK_START.md": "Quick start guide",
        "DATA_INTEGRATION_GUIDE.md": "Comprehensive guide",
        "IMPLEMENTATION_SUMMARY.md": "Implementation details",
    },
    "Generated Data": {
        "data/api_data_aadhar_enrolment.csv": "Enrollment data (5000 records)",
        "data/api_data_aadhar_demographic.csv": "Demographic data (3000 records)",
        "data/api_data_aadhar_biometric.csv": "Biometric data (4500 records)",
    }
}

MODIFIED_FILES = {
    "backend/main.py": "Added data_import router",
    "backend/routes/insights.py": "Enhanced trends-forecast endpoint",
    "requirements.txt": "Added pandas, numpy, scikit-learn",
}


def check_files():
    """Check if all required files exist."""
    print("\n" + "="*70)
    print("AADHAAR PORTAL - IMPLEMENTATION CHECKLIST")
    print("="*70 + "\n")
    
    all_good = True
    
    for category, files in REQUIRED_FILES.items():
        print(f"📋 {category}")
        print("-" * 70)
        
        for file_path, description in files.items():
            full_path = PROJECT_ROOT / file_path
            exists = full_path.exists()
            status = "✅" if exists else "❌"
            
            # For CSV files, also check size
            if file_path.endswith('.csv') and exists:
                size = full_path.stat().st_size
                if size > 10000:  # At least 10KB
                    status = "✅"
                    size_str = f" ({size/1024:.1f} KB)"
                else:
                    status = "⚠️"
                    all_good = False
                    size_str = " (file too small)"
            else:
                size_str = ""
            
            print(f"  {status} {file_path:<40} {description}{size_str}")
            
            if not exists and not file_path.startswith('data/'):
                all_good = False
        
        print()
    
    # Check modified files
    print("📝 Modified Files")
    print("-" * 70)
    for file_path, description in MODIFIED_FILES.items():
        full_path = PROJECT_ROOT / file_path
        exists = full_path.exists()
        status = "✅" if exists else "⚠️"
        print(f"  {status} {file_path:<40} {description}")
    
    print("\n" + "="*70)
    
    if all_good:
        print("✅ ALL COMPONENTS VERIFIED - READY TO USE!")
    else:
        print("⚠️  SOME FILES MISSING - RUN SETUP SCRIPTS")
    
    print("="*70 + "\n")
    
    return all_good


def check_dependencies():
    """Check if required Python packages are installed."""
    print("🔧 Checking Python Dependencies...")
    print("-" * 70)
    
    required = ['pandas', 'numpy', 'sqlalchemy', 'fastapi', 'uvicorn']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✅ {package:<20} installed")
        except ImportError:
            print(f"  ❌ {package:<20} NOT installed")
            missing.append(package)
    
    print()
    
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        print("\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    return True


def show_next_steps():
    """Show next steps."""
    steps = """
📌 NEXT STEPS

1️⃣  GENERATE SAMPLE DATA (if not already done):
    
    python scripts/generate_sample_data.py

2️⃣  UPDATE .env WITH YOUR MYSQL PASSWORD:
    
    DB_PASSWORD=your_mysql_password

3️⃣  CREATE MYSQL DATABASE:
    
    mysql -u root -p"your_password" -e "CREATE DATABASE IF NOT EXISTS aadhaar_analytics;"

4️⃣  INITIALIZE DATABASE & LOAD DATA:
    
    python scripts/setup_complete.py

5️⃣  VERIFY DATA LOADED:
    
    python scripts/verify_database.py

6️⃣  START BACKEND SERVER:
    
    cd backend
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

7️⃣  OPEN DASHBOARD:
    
    http://localhost:8000
    Username: admin
    Password: Admin@1234

✨ That's it! Your Aadhaar Portal is ready with real data!
"""
    print(steps)


def main():
    """Run complete verification."""
    files_ok = check_files()
    print()
    deps_ok = check_dependencies()
    print()
    
    if files_ok and deps_ok:
        print("✅ READY TO START - ALL SYSTEMS GO!")
    else:
        print("⚠️  SETUP INCOMPLETE - FOLLOW INSTRUCTIONS BELOW")
    
    print()
    show_next_steps()


if __name__ == '__main__':
    main()
