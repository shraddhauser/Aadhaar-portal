"""
backend/routes/insights.py
Improvement & insights recommendation endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from backend.database import get_db
from backend.models.models import DailyStat, Anomaly, Region, Enrollment, BiometricData
from backend.routes.auth import get_current_admin

router = APIRouter()


@router.get("/recommendations")
def recommendations(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Rule-based recommendation framework.
    Analyses recent data and returns prioritised action items.
    """
    today    = date.today()
    last_30  = today - timedelta(days=30)
    last_7   = today - timedelta(days=7)

    insights = []

    # --- 1. Low biometric quality ---
    low_quality = db.query(func.count(BiometricData.biometric_id)).filter(
        BiometricData.fingerprint_quality < 60
    ).scalar() or 0
    if low_quality > 0:
        insights.append({
            "category": "Biometric Quality",
            "severity": "High",
            "message":  f"{low_quality} records have fingerprint quality below 60%. "
                        "Recommend calibrating biometric scanners and retraining operators.",
        })

    # --- 2. High rejection rate ---
    total_enroll = db.query(func.count(Enrollment.enrollment_id)).filter(
        Enrollment.enrollment_date >= last_30
    ).scalar() or 1
    rejected = db.query(func.count(Enrollment.enrollment_id)).filter(
        Enrollment.enrollment_date >= last_30,
        Enrollment.enrollment_status == "Rejected",
    ).scalar() or 0
    rejection_rate = (rejected / total_enroll) * 100

    if rejection_rate > 10:
        insights.append({
            "category": "Rejection Rate",
            "severity": "High",
            "message":  f"Rejection rate in last 30 days is {rejection_rate:.1f}%. "
                        "Review document validation rules and operator training.",
        })

    # --- 3. Regions with zero activity ---
    active_regions = db.query(DailyStat.region_id).filter(
        DailyStat.stat_date >= last_7
    ).distinct().subquery()
    inactive = db.query(Region).filter(
        ~Region.region_id.in_(active_regions)
    ).all()
    if inactive:
        names = ", ".join(f"{r.district_name} ({r.state_name})" for r in inactive[:5])
        insights.append({
            "category": "Coverage Gap",
            "severity": "Medium",
            "message":  f"No activity recorded in last 7 days for: {names}. "
                        "Consider deploying mobile enrollment camps.",
        })

    # --- 4. High pending backlog ---
    pending = db.query(func.count(Enrollment.enrollment_id)).filter(
        Enrollment.enrollment_status == "Pending",
        Enrollment.enrollment_date <= today - timedelta(days=3),
    ).scalar() or 0
    if pending > 100:
        insights.append({
            "category": "Processing Backlog",
            "severity": "Medium",
            "message":  f"{pending} enrollments pending for >3 days. "
                        "Increase verification staff or automate document checks.",
        })

    if not insights:
        insights.append({
            "category": "System Health",
            "severity": "Low",
            "message":  "All systems operating normally. No immediate action required.",
        })

    return {"generated_on": str(today), "insights": insights}


@router.get("/biometric-quality")
def biometric_quality_summary(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """Average biometric quality scores across all enrollments."""
    row = db.query(
        func.avg(BiometricData.fingerprint_quality).label("avg_fingerprint"),
        func.avg(BiometricData.iris_quality).label("avg_iris"),
        func.avg(BiometricData.photo_quality).label("avg_photo"),
    ).one()
    return {
        "avg_fingerprint": round(float(row.avg_fingerprint or 0), 1),
        "avg_iris":        round(float(row.avg_iris        or 0), 1),
        "avg_photo":       round(float(row.avg_photo       or 0), 1),
    }


@router.get("/trends-forecast")
def trends_forecast(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Simple predictive trend: compute 3-month simple moving average
    and project next month's enrollment count using growth rate.
    Also integrates machine learning-based forecasts when available.
    """
    from sqlalchemy import extract

    today = date.today()
    # Get monthly totals for last 6 months
    six_months_ago = today.replace(day=1) - timedelta(days=180)

    rows = db.query(
        extract("year", DailyStat.stat_date).label("year"),
        extract("month", DailyStat.stat_date).label("month"),
        func.sum(DailyStat.total_enrollments).label("enrollments"),
        func.sum(DailyStat.total_updates).label("updates"),
    ).filter(
        DailyStat.stat_date >= six_months_ago
    ).group_by("year", "month").order_by("year", "month").all()

    history = [
        {
            "year":        int(r.year),
            "month":       int(r.month),
            "enrollments": int(r.enrollments or 0),
            "updates":     int(r.updates or 0),
        }
        for r in rows
    ]

    # Compute 3-month SMA for enrollment forecast
    enrollment_vals = [h["enrollments"] for h in history]
    if len(enrollment_vals) >= 3:
        sma3 = sum(enrollment_vals[-3:]) / 3
        # Growth rate from last two months
        if enrollment_vals[-2] > 0:
            growth_rate = (enrollment_vals[-1] - enrollment_vals[-2]) / enrollment_vals[-2]
        else:
            growth_rate = 0
        projected = int(sma3 * (1 + growth_rate))
    else:
        sma3 = sum(enrollment_vals) / max(len(enrollment_vals), 1)
        growth_rate = 0
        projected = int(sma3)

    # Machine learning-based forecast (if data available)
    ml_forecast = None
    try:
        from backend.data_ingestion import PredictiveAnalytics
        ml_result = PredictiveAnalytics.forecast_enrollment_trend(db, months_ahead=3)
        if 'forecast' in ml_result:
            ml_forecast = ml_result.get('forecast')
    except:
        pass

    return {
        "history":        history,
        "sma_3_month":    round(sma3, 0),
        "growth_rate_pct": round(growth_rate * 100, 1),
        "projected_next":  projected,
        "ml_forecast":     ml_forecast,
        "model": "Exponential Smoothing + Linear Regression (if ML data available)"
    }


