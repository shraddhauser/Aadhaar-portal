"""
scripts/load_data_to_db.py
Loads generated CSV data into the MySQL database.
Can be run directly or called from the API.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal, engine, Base
from backend.models.models import Region
from backend.data_ingestion import DataIngestionPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database schema."""
    logger.info("Initializing database schema...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database schema created")
    except Exception as e:
        logger.error(f"✗ Error creating schema: {str(e)}")
        return False
    return True


def seed_regions():
    """Seed default regions if not existing."""
    logger.info("Seeding regions...")
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
        existing = db.query(Region).filter(Region.region_code == code).first()
        if not existing:
            region = Region(
                state_name=state,
                district_name=district,
                region_code=code
            )
            db.add(region)
    
    db.commit()
    db.close()
    logger.info("✓ Regions seeded")


def load_data_from_csv(csv_dir: Path):
    """Load data from CSV files in specified directory."""
    logger.info(f"Loading data from {csv_dir}...")
    
    db = SessionLocal()
    pipeline = DataIngestionPipeline(db)
    
    results = {
        'enrollments': {'count': 0, 'errors': []},
        'demographics': {'count': 0, 'errors': []},
        'biometrics': {'count': 0, 'errors': []},
    }
    
    # Load enrollment data
    enroll_file = csv_dir / 'api_data_aadhar_enrolment.csv'
    if enroll_file.exists():
        logger.info(f"Processing {enroll_file}...")
        df = pd.read_csv(enroll_file)
        count, errors = pipeline.ingest_enrollment_data(df)
        results['enrollments']['count'] = count
        results['enrollments']['errors'] = errors
        logger.info(f"✓ Loaded {count} enrollment records")
    else:
        logger.warning(f"✗ Enrollment file not found: {enroll_file}")
    
    # Load demographic data
    demo_file = csv_dir / 'api_data_aadhar_demographic.csv'
    if demo_file.exists():
        logger.info(f"Processing {demo_file}...")
        df = pd.read_csv(demo_file)
        count, errors = pipeline.ingest_demographic_data(df)
        results['demographics']['count'] = count
        results['demographics']['errors'] = errors
        logger.info(f"✓ Loaded {count} demographic records")
    else:
        logger.warning(f"✗ Demographic file not found: {demo_file}")
    
    # Load biometric data
    biometric_file = csv_dir / 'api_data_aadhar_biometric.csv'
    if biometric_file.exists():
        logger.info(f"Processing {biometric_file}...")
        df = pd.read_csv(biometric_file)
        count, errors = pipeline.ingest_biometric_data(df)
        results['biometrics']['count'] = count
        results['biometrics']['errors'] = errors
        logger.info(f"✓ Loaded {count} biometric records")
    else:
        logger.warning(f"✗ Biometric file not found: {biometric_file}")
    
    # Aggregate daily stats
    logger.info("Aggregating daily statistics...")
    stat_count = pipeline.aggregate_daily_stats()
    logger.info(f"✓ Aggregated stats for {stat_count} days")
    
    # Detect anomalies
    logger.info("Detecting anomalies...")
    anomaly_count = pipeline.detect_anomalies()
    logger.info(f"✓ Detected {anomaly_count} anomalies")
    
    db.close()
    return results


def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("AADHAAR PORTAL - DATABASE INITIALIZATION & DATA LOADING")
    print("="*70 + "\n")
    
    # Step 1: Initialize database
    if not init_database():
        logger.error("Failed to initialize database")
        sys.exit(1)
    
    # Step 2: Seed regions
    seed_regions()
    
    # Step 3: Load data from CSV
    data_dir = Path(__file__).parent.parent / 'data'
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        logger.info("Please run: python scripts/generate_sample_data.py")
        sys.exit(1)
    
    results = load_data_from_csv(data_dir)
    
    # Summary
    print("\n" + "="*70)
    print("DATA LOADING SUMMARY")
    print("="*70)
    print(f"Enrollments loaded:  {results['enrollments']['count']:,}")
    print(f"Demographics loaded: {results['demographics']['count']:,}")
    print(f"Biometrics loaded:   {results['biometrics']['count']:,}")
    print(f"\nTotal records: {sum(r['count'] for r in results.values()):,}")
    
    if results['enrollments']['errors']:
        print(f"\nEnrollment errors: {len(results['enrollments']['errors'])}")
    if results['demographics']['errors']:
        print(f"Demographic errors: {len(results['demographics']['errors'])}")
    if results['biometrics']['errors']:
        print(f"Biometric errors: {len(results['biometrics']['errors'])}")
    
    print("\n✓ DATABASE INITIALIZATION COMPLETE")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
