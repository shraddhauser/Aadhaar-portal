# """
# scripts/setup_complete.py
# Complete setup workflow: test DB connection, init schema, load data.
# Shows detailed instructions if MySQL connection fails.
# """

import sys
import os
from pathlib import Path
from subprocess import run, PIPE
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_db_connection():
    """Test database connection using SQLAlchemy."""
    logger.info("Testing database connection...")
    try:
        from sqlalchemy import create_engine, text
        from backend.database import DATABASE_URL, DB_ENGINE, DB_FILE, DB_HOST, DB_PORT, DB_USER

        connect_args = {"check_same_thread": False} if DB_ENGINE == "sqlite" else {}
        engine = create_engine(DATABASE_URL, connect_args=connect_args)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful!")
            if DB_ENGINE == "sqlite":
                logger.info(f"  SQLite file: {DB_FILE}")
            else:
                logger.info(f"  Host: {DB_HOST}:{DB_PORT}")
                logger.info(f"  User: {DB_USER}")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {str(e)}")
        return False


def show_database_setup_instructions():
    """Show database setup instructions."""
    from backend.database import DB_ENGINE

    if DB_ENGINE == "sqlite":
        instructions = (
            "SQLite Database Setup Instructions\n"
            "---------------------------------\n"
            "1. Ensure your `.env` file contains:\n"
            "   DB_ENGINE=sqlite\n"
            "   DB_FILE=./aadhaar_analytics.db\n\n"
            "2. Run the setup script to create the local DB and tables:\n"
            "   python scripts/setup_complete.py\n\n"
            "3. Start the backend server:\n"
            "   cd backend\n"
            "   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload\n\n"
            "4. Open the dashboard:\n"
            "   http://localhost:8000\n"
        )
    else:
        instructions = (
            "MySQL Setup Instructions\n"
            "------------------------\n"
            "1. Ensure MySQL is running on your machine.\n"
            "2. Set/reset the root password if needed and create the `aadhaar_analytics` database.\n"
            "3. Update `.env` with DB_ENGINE=mysql and the connection details.\n"
            "4. Run `python scripts/setup_complete.py` to create schema and load data.\n"
        )

    print(instructions)



def init_database_schema():
    """Initialize database schema."""
    logger.info("Initializing database schema...")
    try:
        # Ensure model modules are imported so their tables are registered
        import backend.models.models  # noqa: F401
        from backend.database import engine, Base
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database schema initialized")
        return True
    except Exception as e:
        logger.error(f"✗ Schema initialization failed: {str(e)}")
        return False


def seed_regions():
    """Seed default regions."""
    logger.info("Seeding regions...")
    try:
        from backend.database import SessionLocal
        from backend.models.models import Region
        
        db = SessionLocal()
        regions_data = [
            ('Maharashtra', 'Mumbai', 'MH-MUM'),
            ('Maharashtra', 'Pune', 'MH-PUN'),
            ('Maharashtra', 'Nashik', 'MH-NSK'),
            ('Karnataka', 'Bengaluru', 'KA-BLR'),
            ('Karnataka', 'Mysuru', 'KA-MYS'),
            ('Tamil Nadu', 'Chennai', 'TN-CHN'),
            ('Tamil Nadu', 'Coimbatore', 'TN-CBE'),
            ('Uttar Pradesh', 'Lucknow', 'UP-LKO'),
            ('Uttar Pradesh', 'Agra', 'UP-AGR'),
            ('Delhi', 'New Delhi', 'DL-NDL'),
        ]
        
        for state, district, code in regions_data:
            if not db.query(Region).filter(Region.region_code == code).first():
                db.add(Region(state_name=state, district_name=district, region_code=code))
        
        db.commit()
        db.close()
        logger.info("✓ Regions seeded")
        return True
    except Exception as e:
        logger.error(f"✗ Seeding failed: {str(e)}")
        return False


def seed_admin_user():
    """Seed a default admin user if not present."""
    logger.info("Seeding admin user...")
    try:
        from backend.database import SessionLocal
        from backend.models.models import AdminUser
        from backend.routes import auth as auth_module

        db = SessionLocal()
        if not db.query(AdminUser).filter(AdminUser.username == 'admin').first():
            pwd_hash = auth_module.pwd_context.hash('Admin@1234')
            admin = AdminUser(username='admin', password_hash=pwd_hash, full_name='Administrator', role='SuperAdmin')
            db.add(admin)
            db.commit()
            logger.info("✓ Admin user created")
        else:
            logger.info("✓ Admin user already exists")
        db.close()
        return True
    except Exception as e:
        logger.error(f"✗ Admin seeding failed: {str(e)}")
        return False


def load_data():
    """Load sample data from CSV."""
    logger.info("Loading sample data...")
    try:
        from backend.database import SessionLocal
        from backend.data_ingestion import DataIngestionPipeline
        import pandas as pd
        
        data_dir = Path(__file__).parent.parent / 'data'
        
        if not data_dir.exists():
            logger.warning("Data directory not found. Run: python scripts/generate_sample_data.py")
            return False
        
        db = SessionLocal()
        pipeline = DataIngestionPipeline(db)
        
        total_loaded = 0
        
        # Load enrollments
        enroll_file = data_dir / 'api_data_aadhar_enrolment.csv'
        if enroll_file.exists():
            logger.info(f"  Loading {enroll_file.name}...")
            df = pd.read_csv(enroll_file)
            count, _ = pipeline.ingest_enrollment_data(df)
            total_loaded += count
            logger.info(f"    ✓ {count:,} records")
        
        # Load demographics
        demo_file = data_dir / 'api_data_aadhar_demographic.csv'
        if demo_file.exists():
            logger.info(f"  Loading {demo_file.name}...")
            df = pd.read_csv(demo_file)
            count, _ = pipeline.ingest_demographic_data(df)
            total_loaded += count
            logger.info(f"    ✓ {count:,} records")
        
        # Load biometrics
        biometric_file = data_dir / 'api_data_aadhar_biometric.csv'
        if biometric_file.exists():
            logger.info(f"  Loading {biometric_file.name}...")
            df = pd.read_csv(biometric_file)
            count, _ = pipeline.ingest_biometric_data(df)
            total_loaded += count
            logger.info(f"    ✓ {count:,} records")
        
        # Aggregate stats
        logger.info("  Aggregating daily statistics...")
        pipeline.aggregate_daily_stats()
        
        # Detect anomalies
        logger.info("  Detecting anomalies...")
        anomaly_count = pipeline.detect_anomalies()
        
        db.close()
        logger.info(f"✓ Data loaded: {total_loaded:,} records, {anomaly_count} anomalies detected")
        return True
    except Exception as e:
        logger.error(f"✗ Data loading failed: {str(e)}")
        return False


def show_final_instructions():
    """Show next steps."""
    instructions = """
SETUP COMPLETE
--------------

NEXT STEPS:

1) Start the backend server:
    cd backend
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

2) Open the dashboard in your browser:
    http://localhost:8000

3) Login credentials:
    Username: admin
    Password: Admin@1234

4) Explore features:
    - Live statistics
    - Historical trends
    - Insights and anomaly alerts

5) API docs:
    http://localhost:8000/docs

6) Read detailed documentation in project files (DATA_INTEGRATION_GUIDE.md, etc.)

"""

    print(instructions)


def main():
    """Run complete setup."""
    print("\n" + "="*70)
    print("AADHAAR PORTAL - COMPLETE SETUP WORKFLOW")
    print("="*70 + "\n")
    
    # Test database connection
    if not test_db_connection():
        show_database_setup_instructions()
        sys.exit(1)
    
    # Initialize schema
    if not init_database_schema():
        logger.error("Setup failed during schema initialization")
        sys.exit(1)
    
    # Seed regions
    if not seed_regions():
        logger.error("Setup failed during region seeding")
        sys.exit(1)

    # Seed default admin user
    if not seed_admin_user():
        logger.error("Setup failed during admin user seeding")
        sys.exit(1)
    
    # Load data
    if not load_data():
        logger.warning("Setup incomplete: Data not loaded")
        logger.info("Run: python scripts/generate_sample_data.py (if not done)")
        logger.info("Then retry: python scripts/setup_complete.py")
        # Don't exit - data can be loaded later via API
    
    # Success
    print("\n" + "="*70)
    show_final_instructions()


if __name__ == '__main__':
    main()

