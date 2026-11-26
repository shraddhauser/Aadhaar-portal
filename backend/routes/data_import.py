"""
backend/routes/data_import.py
API endpoints for data ingestion and predictive analytics.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session
import io
import os
import pandas as pd
import logging

from backend.database import get_db
from backend.data_ingestion import DataIngestionPipeline, PredictiveAnalytics
from backend.routes.auth import require_admin

logger = logging.getLogger(__name__)
# Every /api/import/* route requires a SuperAdmin token.
router = APIRouter(dependencies=[Depends(require_admin)])

DEMO_MODE = os.getenv("DEMO_MODE", "").strip().lower() in ("1", "true", "yes")
MAX_UPLOAD_BYTES = int(float(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024)
_CHUNK = 1024 * 1024

# Each entry is a group of accepted column names; one of them must be present.
REQUIRED_COLUMNS = {
    "enrollment": [
        ("enrollment_date",),
        ("gender",),
        ("age", "age_group"),
        ("region_code", "district"),
    ],
    "demographic": [
        ("update_date",),
        ("update_type",),
        ("region_code", "district"),
    ],
    "biometric": [
        ("enrollment_date",),
        ("fingerprint_quality", "fp_quality"),
        ("iris_quality", "iris_qual"),
        ("photo_quality", "photo_qual"),
    ],
}


async def read_csv_upload(file: UploadFile, kind: str) -> pd.DataFrame:
    """Read an uploaded CSV with size, type and column checks.

    Raises 413 if the file is over MAX_UPLOAD_MB, and 400 if it is empty,
    not a parseable CSV, or missing required columns (listed in the error).
    """
    if DEMO_MODE:
        raise HTTPException(status_code=403, detail="Uploads are disabled in the public demo.")
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv file.")

    contents = bytearray()
    while chunk := await file.read(_CHUNK):
        contents.extend(chunk)
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File is larger than the {MAX_UPLOAD_BYTES / (1024 * 1024):g} MB limit.",
            )
    if not contents.strip():
        raise HTTPException(status_code=400, detail="File is empty.")

    try:
        df = pd.read_csv(io.BytesIO(bytes(contents)))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    columns = {str(c).lower().strip() for c in df.columns}
    missing = [
        " or ".join(group)
        for group in REQUIRED_COLUMNS[kind]
        if not columns.intersection(group)
    ]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={"message": "Missing required columns.", "missing_columns": missing},
        )
    if df.empty:
        raise HTTPException(status_code=400, detail="File has a header row but no data rows.")
    return df


@router.post("/enrollments/upload")
async def upload_enrollment_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and ingest enrollment CSV data.
    Required columns: enrollment_date, gender, age (or age_group),
    region_code (or district). Optional: enrollment_status, aadhaar_generated.
    """
    df = await read_csv_upload(file, "enrollment")
    try:
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
    except Exception:
        logger.exception("Error uploading enrollment data")
        raise  # becomes a JSON 500 via the app's exception handler


@router.post("/demographic/upload")
async def upload_demographic_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and ingest demographic/update CSV data.
    Required columns: update_date, update_type, region_code (or district).
    Optional: update_status.
    """
    df = await read_csv_upload(file, "demographic")
    try:
        pipeline = DataIngestionPipeline(db)
        count, errors = pipeline.ingest_demographic_data(df)

        # Aggregate daily stats
        pipeline.aggregate_daily_stats()

        return {
            "status": "success",
            "records_ingested": count,
            "errors": errors[:10]
        }
    except Exception:
        logger.exception("Error uploading demographic data")
        raise  # becomes a JSON 500 via the app's exception handler


@router.post("/biometric/upload")
async def upload_biometric_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and ingest biometric quality CSV data.
    Required columns: enrollment_date, fingerprint_quality, iris_quality,
    photo_quality.
    """
    df = await read_csv_upload(file, "biometric")
    try:
        pipeline = DataIngestionPipeline(db)
        count, errors = pipeline.ingest_biometric_data(df)

        return {
            "status": "success",
            "records_ingested": count,
            "errors": errors[:10]
        }
    except Exception:
        logger.exception("Error uploading biometric data")
        raise  # becomes a JSON 500 via the app's exception handler


@router.get("/predictive/forecast-enrollment")
def forecast_enrollment(
    months_ahead: int = Query(3, ge=1, le=12),
    db: Session = Depends(get_db),
):
    """
    Forecast enrollment trends for next N months using exponential smoothing.
    """
    result = PredictiveAnalytics.forecast_enrollment_trend(db, months_ahead)
    return result


@router.get("/predictive/growth-patterns")
def identify_growth_patterns(
    db: Session = Depends(get_db),
):
    """
    Identify regions with highest growth and potential issues.
    """
    result = PredictiveAnalytics.identify_growth_patterns(db)
    return result


@router.get("/status")
def ingestion_status(
    db: Session = Depends(get_db),
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
    except Exception:
        logger.exception("Error getting status")
        raise
