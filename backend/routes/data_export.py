"""
backend/routes/data_export.py
Data export endpoint — server-side report generation.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from backend.database import get_db
from backend.models.models import DailyStat, Enrollment, Update, Region, Anomaly
from backend.routes.auth import get_current_admin

router = APIRouter()


@router.get("/summary-report")
def summary_report(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
):
    """
    Generate a JSON summary of key portal metrics
    suitable for rendering into a PDF on the frontend.
    """
    today   = date.today()
    last_30 = today - timedelta(days=30)

    # KPI totals for the last 30 days
    stats = db.query(
        func.sum(DailyStat.total_enrollments).label("enrollments"),
        func.sum(DailyStat.total_updates).label("updates"),
        func.sum(DailyStat.aadhaar_generated).label("generated"),
        func.sum(DailyStat.pending_count).label("pending"),
        func.sum(DailyStat.rejected_count).label("rejected"),
    ).filter(DailyStat.stat_date >= last_30).one()

    # Top 5 regions
    top_regions = db.query(
        Region.state_name,
        Region.district_name,
        func.sum(DailyStat.total_enrollments).label("enrollments"),
    ).join(DailyStat, DailyStat.region_id == Region.region_id
    ).filter(DailyStat.stat_date >= last_30
    ).group_by(Region.region_id
    ).order_by(func.sum(DailyStat.total_enrollments).desc()
    ).limit(5).all()

    # Unresolved anomalies count
    anomaly_count = db.query(func.count(Anomaly.anomaly_id)).filter(
        Anomaly.resolved == False
    ).scalar() or 0

    return {
        "report_date": str(today),
        "period":      f"{last_30} to {today}",
        "kpis": {
            "enrollments": int(stats.enrollments or 0),
            "updates":     int(stats.updates or 0),
            "generated":   int(stats.generated or 0),
            "pending":     int(stats.pending or 0),
            "rejected":    int(stats.rejected or 0),
        },
        "top_regions": [
            {
                "state":       r.state_name,
                "district":    r.district_name,
                "enrollments": int(r.enrollments or 0),
            }
            for r in top_regions
        ],
        "unresolved_anomalies": anomaly_count,
    }
