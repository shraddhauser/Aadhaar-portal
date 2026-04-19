"""
backend/routes/data_import.py
API endpoints for data ingestion and predictive analytics.
"""

from fastapi import APIRouter, Depends, File, UploadFile, Query
from sqlalchemy.orm import Session
import io
import pandas as pd
import logging

from backend.database import get_db
from backend.data_ingestion import DataIngestionPipeline, PredictiveAnalytics
from backend.routes.auth import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/enrollments/upload")
async def upload_enrollment_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Upload and ingest enrollment CSV data.
    Expected columns: enrollment_date, gender, age, enrollment_status, region_code
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        pipeline = DataIngestionPipeline(db)
        count, errors = pipeline.ingest_enrollment_data(df)
        
        # Aggregate daily stats after ingestion
        pipeline.aggregate_daily_stats()
        
        # Detect anomalies
        anomaly_count = pipeline.detect_anomalies()
        
        return {
            "status": "success",
            "records_ingested": count,
            "anomalies_detected": anomaly_count,
            "errors": errors[:10]  # Return first 10 errors
        }
    except Exception as e:
        logger.error(f"Error uploading enrollment data: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "records_ingested": 0
        }


@router.post("/demographic/upload")
async def upload_demographic_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Upload and ingest demographic/update CSV data.
    Expected columns: update_date, update_type, update_status, region_code
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        pipeline = DataIngestionPipeline(db)
        count, errors = pipeline.ingest_demographic_data(df)
        
        # Aggregate daily stats
        pipeline.aggregate_daily_stats()
        
        return {
            "status": "success",
            "records_ingested": count,
            "errors": errors[:10]
        }
    except Exception as e:
        logger.error(f"Error uploading demographic data: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "records_ingested": 0
        }


@router.post("/biometric/upload")
async def upload_biometric_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Upload and ingest biometric quality CSV data.
    Expected columns: fingerprint_quality, iris_quality, photo_quality, enrollment_date
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        pipeline = DataIngestionPipeline(db)
        count, errors = pipeline.ingest_biometric_data(df)
        
        return {
            "status": "success",
            "records_ingested": count,
            "errors": errors[:10]
        }
    except Exception as e:
        logger.error(f"Error uploading biometric data: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "records_ingested": 0
        }


@router.get("/predictive/forecast-enrollment")
def forecast_enrollment(
    months_ahead: int = Query(3, ge=1, le=12),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Forecast enrollment trends for next N months using exponential smoothing.
    """
    result = PredictiveAnalytics.forecast_enrollment_trend(db, months_ahead)
    return result


@router.get("/predictive/growth-patterns")
def identify_growth_patterns(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Identify regions with highest growth and potential issues.
    """
    result = PredictiveAnalytics.identify_growth_patterns(db)
    return result


@router.get("/status")
def ingestion_status(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Get current data ingestion status and counts.
    """
    from backend.models.models import Enrollment, Update, BiometricData, DailyStat
    from sqlalchemy import func
    
    try:
        enrollment_count = db.query(func.count(Enrollment.enrollment_id)).scalar() or 0
        update_count = db.query(func.count(Update.update_id)).scalar() or 0
        biometric_count = db.query(func.count(BiometricData.biometric_id)).scalar() or 0
        daily_stat_count = db.query(func.count(DailyStat.stat_id)).scalar() or 0
        
        return {
            "enrollments": int(enrollment_count),
            "updates": int(update_count),
            "biometric_records": int(biometric_count),
            "daily_stats": int(daily_stat_count),
            "total_records": int(enrollment_count + update_count + biometric_count)
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {"error": str(e)}
