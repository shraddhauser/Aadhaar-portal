"""
scripts/verify_database.py
Verify that real data is loaded in the database.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def verify_database():
    """Verify database and show data stats."""
    try:
        from backend.database import SessionLocal
        from backend.models.models import (
            Region, Enrollment, Update, BiometricData,
            DailyStat, Anomaly, AdminUser
        )
        from sqlalchemy import func
        
        db = SessionLocal()
        
        print("\n" + "="*70)
        print("DATABASE VERIFICATION REPORT")
        print("="*70 + "\n")
        
        # Regions
        region_count = db.query(func.count(Region.region_id)).scalar() or 0
        logger.info(f"🟢 Regions: {int(region_count)}")
        if region_count > 0:
            regions = db.query(Region).limit(5).all()
            for r in regions:
                logger.info(f"   • {r.region_code}: {r.district_name}, {r.state_name}")
            if region_count > 5:
                logger.info(f"   ... and {int(region_count)-5} more")
        
        # Enrollments
        enroll_count = db.query(func.count(Enrollment.enrollment_id)).scalar() or 0
        logger.info(f"\n🟢 Enrollments: {int(enroll_count):,}")
        if enroll_count > 0:
            # Gender breakdown
            gender_stats = db.query(
                Enrollment.gender,
                func.count(Enrollment.enrollment_id).label("count")
            ).group_by(Enrollment.gender).all()
            for gender, count in gender_stats:
                pct = (count / enroll_count) * 100
                logger.info(f"   • {gender}: {int(count):,} ({pct:.1f}%)")
            
            # Status breakdown
            logger.info("   Status breakdown:")
            status_stats = db.query(
                Enrollment.enrollment_status,
                func.count(Enrollment.enrollment_id).label("count")
            ).group_by(Enrollment.enrollment_status).all()
            for status, count in status_stats:
                logger.info(f"     - {status}: {int(count):,}")
            
            # Date range
            from sqlalchemy import func as sqlfunc
            first_date = db.query(func.min(Enrollment.enrollment_date)).scalar()
            last_date = db.query(func.max(Enrollment.enrollment_date)).scalar()
            logger.info(f"   Date range: {first_date} to {last_date}")
        
        # Updates
        update_count = db.query(func.count(Update.update_id)).scalar() or 0
        logger.info(f"\n🟢 Updates: {int(update_count):,}")
        if update_count > 0:
            # Update types
            type_stats = db.query(
                Update.update_type,
                func.count(Update.update_id).label("count")
            ).group_by(Update.update_type).order_by(func.count(Update.update_id).desc()).all()
            logger.info("   Top update types:")
            for update_type, count in type_stats[:5]:
                logger.info(f"   • {update_type}: {int(count):,}")
        
        # Biometric Data
        biometric_count = db.query(func.count(BiometricData.biometric_id)).scalar() or 0
        logger.info(f"\n🟢 Biometric Records: {int(biometric_count):,}")
        if biometric_count > 0:
            bio_stats = db.query(
                func.avg(BiometricData.fingerprint_quality).label("avg_fp"),
                func.avg(BiometricData.iris_quality).label("avg_iris"),
                func.avg(BiometricData.photo_quality).label("avg_photo"),
                func.min(BiometricData.fingerprint_quality).label("min_fp"),
                func.max(BiometricData.fingerprint_quality).label("max_fp"),
            ).one()
            logger.info(f"   Fingerprint Quality: avg={bio_stats.avg_fp:.1f}% (min={bio_stats.min_fp}, max={bio_stats.max_fp})")
            logger.info(f"   Iris Quality: avg={bio_stats.avg_iris:.1f}%")
            logger.info(f"   Photo Quality: avg={bio_stats.avg_photo:.1f}%")
        
        # Daily Stats
        daily_count = db.query(func.count(DailyStat.stat_id)).scalar() or 0
        logger.info(f"\n🟢 Daily Statistics: {int(daily_count)} days")
        if daily_count > 0:
            daily_stats = db.query(
                func.sum(DailyStat.total_enrollments).label("total_enroll"),
                func.sum(DailyStat.total_updates).label("total_updates"),
                func.sum(DailyStat.aadhaar_generated).label("total_generated"),
            ).one()
            logger.info(f"   Total enrollments (aggregated): {int(daily_stats.total_enroll or 0):,}")
            logger.info(f"   Total updates (aggregated): {int(daily_stats.total_updates or 0):,}")
            logger.info(f"   Total generated (aggregated): {int(daily_stats.total_generated or 0):,}")
        
        # Anomalies
        anomaly_count = db.query(func.count(Anomaly.anomaly_id)).scalar() or 0
        logger.info(f"\n🟢 Anomalies Detected: {int(anomaly_count)}")
        if anomaly_count > 0:
            anomalies = db.query(Anomaly).limit(5).all()
            for anom in anomalies:
                logger.info(f"   • [{anom.severity}] {anom.anomaly_type}: {anom.description}")
        
        # Admin Users
        admin_count = db.query(func.count(AdminUser.admin_id)).scalar() or 0
        logger.info(f"\n🟢 Admin Users: {int(admin_count)}")
        
        # Summary
        total_records = int(enroll_count + update_count + biometric_count)
        logger.info("\n" + "="*70)
        logger.info(f"TOTAL RECORDS IN DATABASE: {total_records:,}")
        logger.info("="*70 + "\n")
        
        if total_records > 0:
            logger.info("✓ DATABASE IS READY FOR ANALYTICS!")
            logger.info("\nTo start the backend:")
            logger.info("  cd backend")
            logger.info("  python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
            logger.info("\nThen open: http://localhost:8000")
            return True
        else:
            logger.warning("✗ No data found in database")
            logger.info("\nTo load sample data:")
            logger.info("  python scripts/generate_sample_data.py")
            logger.info("  python scripts/load_data_to_db.py")
            return False
        
    except Exception as e:
        logger.error(f"✗ Database connection failed: {str(e)}")
        logger.info("\nPlease ensure:")
        logger.info("  1. MySQL is running")
        logger.info("  2. .env file has correct credentials")
        logger.info("  3. Database 'aadhaar_analytics' exists")
        return False


if __name__ == '__main__':
    success = verify_database()
    sys.exit(0 if success else 1)
